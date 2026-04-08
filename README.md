# Pylandstats-Interface
Interface to calculate metrics for pylandstats
# 🌿 Landscape Analysis 

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-FF4B4B.svg)](https://streamlit.io/)
[![PyLandStats](https://img.shields.io/badge/PyLandStats-3.1.0-green.svg)](https://pylandstats.readthedocs.io/)

**Landscape Analysis Interface** est une interface interactive et performante dédiée à l'écologie du paysage. Elle permet de calculer des métriques spatiales complexes sur des rasters d'occupation du sol en utilisant des unités spatiales personnalisées (grilles, polygones, parcelles).

L'application est optimisée pour le traitement de grands jeux de données grâce à une gestion de la mémoire par **"Chunk Processing"** (traitement par blocs).

## ✨ Caractéristiques

* **📊 Analyse Zonale complète** : Calcul de métriques au niveau de la classe et du paysage.
* **🧩 5 Catégories de Métriques** :
    * *Area & Edge* (Surface, Densité, Lisières)
    * *Shape* (Complexité des formes)
    * *Core* (Zones cœurs)
    * *Aggregation* (Connectivité et proximité)
    * *Diversity* (Indices de Shannon, Entropie, Contagion)
* **🚀 Optimisation RAM** : Traitement par morceaux (chunks) pour éviter les crashs sur les très grands rasters.
* **🖥️ Console Live** : Suivi en temps réel de l'avancement des calculs.
* **💾 Multi-Format** : Export automatique en `.csv` et `.gpkg` (GeoPackage) pour une intégration directe dans QGIS ou ArcGIS.
* **🪟 Cross-Platform** : Compatible Linux et Windows.

## 🛠️ Installation

### 1. Prérequis
Il est recommandé d'utiliser un environnement virtuel (Conda ou venv).

# Créer l'environnement
conda create -n landscape_env python=3.10 -y
conda activate landscape_env

# Installer les dépendances géospatiales
conda install -c conda-forge geopandas rasterio pyogrio -y

# Installer l'interface et le moteur de calcul
pip install pylandstats streamlit

2. Lancement


streamlit run app.py

🚀 Utilisation

    Work Directory : Définissez votre dossier de travail (les chemins se mettront à jour automatiquement).

    Inputs : Chargez votre Raster (.tif) et vos Unités Spatiales (.shp ou .gpkg).

    Metrics : Cochez les métriques souhaitées dans les 5 colonnes.

    Run : Utilisez le mode TEST (500 lignes) pour vérifier vos données, puis lancez l'ANALYSE COMPLÈTE.

📂 Structure du projet

    app.py : Le code source principal de l'application Streamlit.

    Lancer_Analyse.bat : Script de lancement rapide pour Windows.

    temp_chunk_results.csv : Fichier temporaire généré pendant le calcul par blocs.
📝 Auteur

    Kheobs - Initial work Matthew MARTINE
