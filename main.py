import streamlit as st
import pylandstats as pls
import geopandas as gpd
import rasterio
import os
import time
import pandas as pd
import gc  # Garbage Collector pour vider la RAM

# --- CONFIGURATION ---
st.set_page_config(page_title="Landscape Analysis", layout="wide")

# Style CSS pour le terminal et les cases
st.markdown("""
    <style>
    .stCode { background-color: #0e1117 !important; color: #00FF00 !important; }
    .stCheckbox { margin-bottom: -8px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 Landscape Analysis")

# --- SIDEBAR: PATHS & SETTINGS ---
st.sidebar.header("📂 Data Source & Export")

work_dir = st.sidebar.text_input(
    "Work & Export Directory", 
    value=r"/home/kheobs/Desktop/landscapemetrics/mainland_southeastasia/"
)

raster_path = st.sidebar.text_input(
    "Landscape Raster (.tif)", 
    value=os.path.join(work_dir, "Region_lulc_2024_merged_compress_reclass_clipreprojected.tif")
)
vector_path = st.sidebar.text_input(
    "Spatial Analysis Unit (.gpkg, .shp)", 
    value=os.path.join(work_dir, "grid_SA_clipreprojected.gpkg")
)
target_classes_str = st.sidebar.text_input("Target Classes (e.g., 1, 2, 3)", "1, 2, 3, 4, 5, 6, 7")

# Taille des morceaux pour la RAM
CHUNK_SIZE = st.sidebar.number_input("Chunk Size (Cells per batch)", value=5000, step=1000)

# --- CENTER: METRICS SELECTION ---
st.subheader("📊 Metrics Selection")

cat_area = {
    'total_area': 'Total Area (total_area)',
    'proportion_of_landscape': 'Proportion of Landscape (proportion_of_landscape)',
    'number_of_patches': 'Number of Patches (number_of_patches)',
    'patch_density': 'Patch Density (patch_density)',
    'largest_patch_index': 'Largest Patch Index (largest_patch_index)',
    'total_edge': 'Total Edge (total_edge)',
    'edge_density': 'Edge Density (edge_density)',
    'area_mn': 'Mean Patch Area (area_mn)',
    'perimeter_mn': 'Mean Perimeter (perimeter_mn)'
}

cat_shape = {
    'shape_index_mn': 'Mean Shape Index (shape_index_mn)',
    'perimeter_area_ratio_mn': 'Mean Perimeter-Area Ratio (perimeter_area_ratio_mn)',
    'fractal_dimension_mn': 'Mean Fractal Dimension (fractal_dimension_mn)'
}

cat_core = {
    'total_core_area': 'Total Core Area (total_core_area)',
    'core_area_proportion_of_landscape': 'Core Area Prop. of Landscape (core_area_proportion_of_landscape)',
    'number_of_disjunct_core_areas': 'Number of Disjunct Core Areas (number_of_disjunct_core_areas)',
    'disjunct_core_area_density': 'Disjunct Core Area Density (disjunct_core_area_density)',
    'core_area_mn': 'Mean Core Area (core_area_mn)'
}

cat_aggregation = {
    'landscape_shape_index': 'Landscape Shape Index (landscape_shape_index)',
    'effective_mesh_size': 'Effective Mesh Size (effective_mesh_size)',
    'euclidean_nearest_neighbor_mn': 'Mean Euclidean Nearest Neighbor (euclidean_nearest_neighbor_mn)'
}

cat_landscape = {
    'shannon_diversity_index': 'Shannon Diversity Index (shannon_diversity_index)',
    'entropy': 'Entropy (entropy)',
    'contagion': 'Contagion (contagion)',
    'joint_entropy': 'Joint Entropy (joint_entropy)',
    'conditional_entropy': 'Conditional Entropy (conditional_entropy)',
    'mutual_information': 'Mutual Information (mutual_information)',
    'relative_mutual_information': 'Relative Mutual Information (relative_mutual_information)'
}

selected_class_metrics = []
selected_landscape_metrics = []

cols = st.columns(5)
with cols[0]:
    st.markdown("**📏 Area & Edge**")
    for k, v in cat_area.items():
        if st.checkbox(v, value=(k in ['proportion_of_landscape', 'patch_density']), key=k): selected_class_metrics.append(k)
with cols[1]:
    st.markdown("**📐 Shape**")
    for k, v in cat_shape.items():
        if st.checkbox(v, value=(k == 'shape_index_mn'), key=k): selected_class_metrics.append(k)
with cols[2]:
    st.markdown("**🎯 Core**")
    for k, v in cat_core.items():
        if st.checkbox(v, value=False, key=k): selected_class_metrics.append(k)
with cols[3]:
    st.markdown("**🔗 Aggregation**")
    for k, v in cat_aggregation.items():
        if st.checkbox(v, value=False, key=k): selected_class_metrics.append(k)
with cols[4]:
    st.markdown("**📊 Landscape-level metrics**")
    for k, v in cat_landscape.items():
        if st.checkbox(v, value=(k == 'shannon_diversity_index'), key=k): selected_landscape_metrics.append(k)

st.divider()

# --- PROCESSING ---
st.subheader("🖥️ Live Processing Console")
terminal_placeholder = st.empty()

def update_terminal(message, state_log):
    timestamp = time.strftime("%H:%M:%S")
    new_line = f"[{timestamp}] {message}"
    state_log.append(new_line)
    terminal_placeholder.code("\n".join(state_log[-8:]), language="bash")

def run_analysis(is_test=False):
    if not selected_class_metrics and not selected_landscape_metrics:
        st.error("Select at least one metric!")
        return
    
    log_history = []
    try:
        # 1. Chargement de la grille (Limitée si test)
        update_terminal("▶️ Loading Vector Spatial Units...", log_history)
        grid = gpd.read_file(vector_path, engine="pyogrio", fid_as_index=True, rows=500 if is_test else None)
        grid['fid'] = grid.index
        total_rows = len(grid)
        
        classes_list = [int(x.strip()) for x in target_classes_str.split(",")]
        temp_csv = os.path.join(work_dir, "temp_chunk_results.csv")
        
        # Supprimer l'ancien fichier temporaire s'il existe
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
            
        t0 = time.time()
        
        # 2. Boucle par CHUNKS pour économiser la RAM
        current_chunk_size = 500 if is_test else CHUNK_SIZE
        update_terminal(f"Starting analysis on {total_rows} cells (Chunk: {current_chunk_size})...", log_history)
        
        progress_bar = st.progress(0)
        
        for start_idx in range(0, total_rows, current_chunk_size):
            end_idx = min(start_idx + current_chunk_size, total_rows)
            update_terminal(f"Processing chunk: {start_idx} to {end_idx}...", log_history)
            
            grid_chunk = grid.iloc[start_idx:end_idx]
            
            # Initialisation de l'analyse zonale pour ce morceau
            za = pls.ZonalAnalysis(landscape_filepath=raster_path, zones=grid_chunk, zone_index='fid')
            df_chunk = pd.DataFrame(index=grid_chunk.index)

            # Calculs Class-level
            if selected_class_metrics:
                res_c = za.compute_class_metrics_df(metrics=selected_class_metrics, classes=classes_list)
                res_c_wide = res_c.unstack(level='class_val')
                res_c_wide.columns = [f"class_{cls}_{m}" for m, cls in res_c_wide.columns]
                df_chunk = df_chunk.join(res_c_wide)

            # Calculs Landscape-level
            if selected_landscape_metrics:
                res_l = za.compute_landscape_metrics_df(metrics=selected_landscape_metrics)
                df_chunk = df_chunk.join(res_l)

            # Sauvegarde incrémentielle dans le CSV
            df_chunk = df_chunk.fillna(0).round(4)
            write_header = (start_idx == 0)
            df_chunk.to_csv(temp_csv, mode='a', header=write_header)
            
            # Nettoyage RAM après chaque morceau
            del za, df_chunk, grid_chunk
            gc.collect()
            
            progress_bar.progress(end_idx / total_rows)

        # 3. Finalisation et Export
        update_terminal("✅ All chunks processed. Finalizing files...", log_history)
        
        # On recharge le résultat complet depuis le CSV
        df_final_results = pd.read_csv(temp_csv, index_col=0)
        
        st.subheader(f"📋 Metrics Preview ({'Test 500 rows' if is_test else 'Full Analysis'})")
        st.dataframe(df_final_results.head(100), use_container_width=True)

        st.markdown("### 📥 Download & Save")
        c1, c2 = st.columns(2)
        
        # Bouton CSV (Toujours actif)
        csv_bytes = df_final_results.to_csv().encode('utf-8')
        c1.download_button(f"Download {'TEST' if is_test else 'Full'} CSV", csv_bytes, "metrics_results.csv")
        
        if not is_test:
            # Création du GeoPackage final
            out_gpkg = os.path.join(work_dir, "analysis_results_final.gpkg")
            final_spatial = grid.drop(columns=['fid']).join(df_final_results)
            final_spatial.to_file(out_gpkg, driver="GPKG")
            
            with open(out_gpkg, "rb") as f:
                c2.download_button("Download Full GeoPackage", f, "landscape_results.gpkg")
            st.success(f"Final files saved in: {work_dir}")
        else:
            st.warning("⚠️ Test Mode: GeoPackage file creation skipped. Download the CSV above to verify results.")

    except Exception as e:
        update_terminal(f"🚨 ERROR: {str(e)}", log_history)
        st.error(e)

# --- ACTION BUTTONS ---
st.sidebar.markdown("---")
if st.sidebar.button("🛠️ RUN TEST (500 ROWS)", use_container_width=True):
    run_analysis(is_test=True)
if st.sidebar.button("🚀 RUN FULL ANALYSIS (CHUNK MODE)", type="primary", use_container_width=True):
    run_analysis(is_test=False)
