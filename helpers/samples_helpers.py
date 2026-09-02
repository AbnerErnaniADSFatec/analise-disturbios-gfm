import folium
import gdown
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from folium.plugins import Fullscreen
from helpers.samples_helpers import *
from helpers.simplecube_helpers import *
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPolygon
import xml.etree.ElementTree as ET
import pandas as pd

def count_values_tif(tiff):
    print("Cropped shape:", subset.shape)
    unique_vals, counts = np.unique(subset.values, return_counts=True)
    print("\nUnique values and pixel counts:")
    for val, count in zip(unique_vals, counts):
        print(f"Value: {val:<6} | Pixels: {count}")

def plot_balance(df, class_column, title = "Distribuição das Classes"):
    class_counts = df[class_column].value_counts()
    plt.figure(figsize=(8, 8))
    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f'{pct:.1f}%\n({val:,})'
        return my_autopct
    plt.pie(
        class_counts.values,
        labels=class_counts.index,
        autopct=make_autopct(class_counts.values),
        startangle=140,
        colors=plt.cm.Set2.colors,  # Paleta de cores suave
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
    )
    plt.title(title, fontsize=14, pad=20)
    plt.tight_layout()
    plt.show()

def extract_qml_legend(qml_path):
    """
    Extrai a legenda (valor, label, cor, alpha) de um arquivo .qml do QGIS.
    Funciona para renderizadores do tipo 'paletted' e 'singlebandpseudocolor'.
    """
    tree = ET.parse(qml_path)
    root = tree.getroot()
    
    legend_entries = []
    
    # Busca tanto paletteEntry (paletted) quanto item (singlebandpseudocolor)
    entries = root.findall(".//paletteEntry") or root.findall(".//item")
    
    for entry in entries:
        val = entry.get("value")
        label = entry.get("label")
        color = entry.get("color")
        alpha = entry.get("alpha", "255")
        
        if val is not None and label is not None:
            try:
                legend_entries.append({
                    "value": float(val),
                    "int_value": int(float(val)),
                    "label": label,
                    "color": color,
                    "alpha": int(alpha)
                })
            except ValueError:
                continue
                
    df_legend = pd.DataFrame(legend_entries)
    
    # Cria também um dicionário rápido {valor_float: nome_da_classe}
    mapping_dict = {row["value"]: row["label"] for row in legend_entries}
    
    return mapping_dict, df_legend

def extract_samples_from_tiff(da, mask, year, n_samples, tile = None):
    subset = da
    tile_id = "No tile"
    if tile is not None and not tile.empty:
        min_lon, min_lat, max_lon, max_lat = tile.total_bounds
        subset = amazonia_class.rio.clip_box(
            minx=min_lon,
            miny=min_lat,
            maxx=max_lon,
            maxy=max_lat
        ).squeeze().compute()    
        tile_id = tile.iloc[0].id        
    
    TARGET_CLASSES = mask
    SAMPLES_PER_CLASS = n_samples  # Number of points per class
    records = []
    
    # Get 1D coordinate arrays
    x_coords = subset.x.values
    y_coords = subset.y.values
    raster_values = subset.values
    
    for class_id, class_name in TARGET_CLASSES.items():
        # Find row (y) and column (x) indices matching the class
        row_idx, col_idx = np.where(raster_values == class_id)
        
        total_pixels = len(row_idx)
        if total_pixels == 0:
            print(f"Class {class_name} ({class_id}) not found in this tile.")
            continue
        
        # Sample with or without replacement based on class abundance
        sample_size = min(SAMPLES_PER_CLASS, total_pixels)
        selected_indices = np.random.choice(total_pixels, size=sample_size, replace=False)
        
        # Map pixel indices to geospatial coordinates
        sampled_xs = x_coords[col_idx[selected_indices]]
        sampled_ys = y_coords[row_idx[selected_indices]]
        
        for x, y in zip(sampled_xs, sampled_ys):
            records.append({
                "year": year,
                "label": class_name,
                "tile": tile_id,
                "geometry": Point(x, y)
            })
    
    # Create GeoDataFrame
    if len(records) > 0:
        df = pd.DataFrame(records)
        samples_gdf = gpd.GeoDataFrame(
            df, 
            geometry="geometry", 
            crs=da.rio.crs if da.rio.crs else "EPSG:4326"
        )
    else:
        # Create an empty GeoDataFrame with predefined schema if no points were sampled
        samples_gdf = gpd.GeoDataFrame(
            columns=["year", "label", "tile", "geometry"],
            geometry="geometry",
            crs=da.rio.crs if da.rio.crs else "EPSG:4326"
        )
        print("Warning: No matching sample points were found. Resulting GeoDataFrame is empty.")
    return samples_gdf
    