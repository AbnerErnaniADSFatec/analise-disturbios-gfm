import json
import os
import urllib

import folium
import geemap.foliumap as geemap
import geopandas as gpd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pystac_client
import rasterio
import requests
import rioxarray
import seaborn
import xarray as xr
from geotessera import GeoTessera
from helpers.simplecube import load_xarray, save_xarray, simple_cube
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import Affine
from scipy.signal import savgol_filter
from shapely.geometry import MultiPoint, MultiPolygon, Point, Polygon
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, RobustScaler

#### ======================== To plot embeddings

# 3. Cria o mapa interativo
Map = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")

# 4. Adiciona a camada de satélite como base opcional
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google Satellite",
    name="Google Satellite"
).add_to(Map)

plot_embeddings_rgb_folium(
    tessera_mosaic_embeddings,
    (0, 5, 6)
).add_to(Map)

plot_pca_rgb_folium(
    tessera_mosaic_embeddings_pca_rgb
).add_to(Map)

folium.GeoJson(
    tile,
    name=f"Tile {tile_id_}",
    style_function=lambda feature: {
        "fillColor": "#ff7800",
        "color": "#000000",       # Cor da borda
        "weight": 2,              # Espessura da borda
        "fillOpacity": 0.2,       # Transparência do preenchimento
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[col for col in tile.columns if col != "geometry"][:3],  # Mostra até 3 colunas de atributos
        localize=True
    )
).add_to(Map)

folium.LayerControl().add_to(Map)

Map

#### ======================== To plot samples

# 3. Cria o mapa interativo
Map = folium.Map(location=center, zoom_start=12, tiles="OpenStreetMap")

# 4. Adiciona a camada de satélite como base opcional
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google Satellite",
    name="Google Satellite"
).add_to(Map)

# ============== Teste Tile ==============
folium.GeoJson(
    test_tile,
    name=f"Test Tile {test_tile_id}",
    style_function=lambda feature: {
        "fillColor": "#ff7800",
        "color": "#000000",       # Cor da borda
        "weight": 2,              # Espessura da borda
        "fillOpacity": 0.2,       # Transparência do preenchimento
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[col for col in test_tile.columns if col != "geometry"][:3],  # Mostra até 3 colunas de atributos
        localize=True
    )
).add_to(Map)

folium.GeoJson(
    test_samples,
    name=f"Test Samples Distúrbios {label} {year}",
    style_function=lambda feature: {
        "fillColor": "#ff7800",
        "color": "#000000",       # Cor da borda
        "weight": 2,              # Espessura da borda
        "fillOpacity": 0.2,       # Transparência do preenchimento
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[col for col in samples.columns if col != "geometry"][:3],  # Mostra até 3 colunas de atributos
        localize=True
    )
).add_to(Map)

folium.GeoJson(
    test_samples_points,
    name=f"Test Samples Points Distúrbios {label} {year}",
    style_function=lambda feature: {
        "fillColor": "#ff7800",
        "color": "#000000",       # Cor da borda
        "weight": 2,              # Espessura da borda
        "fillOpacity": 0.2,       # Transparência do preenchimento
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[col for col in samples.columns if col != "geometry"][:3],  # Mostra até 3 colunas de atributos
        localize=True
    )
).add_to(Map)

# ============== ROI 1 Tile ==============
folium.GeoJson(
    roi_tile_1,
    name=f"ROI 1 Tile {roi_tile_1_id}",
    style_function=lambda feature: {
        "fillColor": "#ff7800",
        "color": "#000000",       # Cor da borda
        "weight": 2,              # Espessura da borda
        "fillOpacity": 0.2,       # Transparência do preenchimento
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[col for col in roi_tile_1.columns if col != "geometry"][:3],  # Mostra até 3 colunas de atributos
        localize=True
    )
).add_to(Map)

folium.GeoJson(
    roi_samples_tile_1,
    name=f"ROI 1 Samples Distúrbios {label} {year}",
    style_function=lambda feature: {
        "fillColor": "#ff7800",
        "color": "#000000",       # Cor da borda
        "weight": 2,              # Espessura da borda
        "fillOpacity": 0.2,       # Transparência do preenchimento
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[col for col in roi_samples_tile_1.columns if col != "geometry"][:3],  # Mostra até 3 colunas de atributos
        localize=True
    )
).add_to(Map)

# ============== ROI 2 Tile ==============
folium.GeoJson(
    roi_tile_2,
    name=f"ROI 2 Tile {roi_tile_2_id}",
    style_function=lambda feature: {
        "fillColor": "#ff7800",
        "color": "#000000",       # Cor da borda
        "weight": 2,              # Espessura da borda
        "fillOpacity": 0.2,       # Transparência do preenchimento
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[col for col in roi_tile_2.columns if col != "geometry"][:3],  # Mostra até 3 colunas de atributos
        localize=True
    )
).add_to(Map)

folium.GeoJson(
    roi_samples_tile_2,
    name=f"ROI 2 Samples Distúrbios {label} {year}",
    style_function=lambda feature: {
        "fillColor": "#ff7800",
        "color": "#000000",       # Cor da borda
        "weight": 2,              # Espessura da borda
        "fillOpacity": 0.2,       # Transparência do preenchimento
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[col for col in roi_samples_tile_2.columns if col != "geometry"][:3],  # Mostra até 3 colunas de atributos
        localize=True
    )
).add_to(Map)

Fullscreen(
    position="topright",
    title="Expand me",
    title_cancel="Exit me",
    force_separate_button=True,
).add_to(Map)

folium.LayerControl().add_to(Map)

Map