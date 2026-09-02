import json
import os
import sys
from pathlib import Path

import ee
import folium
import geemap.foliumap as geemap
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import rasterio.transform
import rioxarray
import shapely.ops
import xarray as xr
from geotessera import GeoTessera, dequantize_embedding
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import Affine, from_bounds
from rioxarray.merge import merge_arrays
from shapely.geometry import Point
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, RobustScaler, normalize


def create_tessera_mosaic(gt_object, year: int, bbox: list[float]) -> xr.DataArray:
  """Monta o mosaico Tessera a partir dos arquivos salvos localmente,

  reprojeta para WGS84 e recorta para o bbox solicitado.

  Args:
      year: Ano de referência dos blocos.
      bbox: Limites no formato [minx, miny, maxx, maxy] em coordenadas EPSG:4326.

  Returns:
      xr.DataArray: Mosaico final recortado na área de interesse em EPSG:4326.
  """
  # 1. Busca todos os blocos dentro do bbox global
  tiles_to_fetch = gt_object.registry.load_blocks_for_region(bounds=bbox, year=year)
  tiles = gt_object.fetch_embeddings(tiles_to_fetch)

  if not tiles:
    raise ValueError(
        f"Nenhum bloco encontrado para o ano {year} e bbox {bbox}."
    )

  tile_arrays = []

  # 2. Carrega, dequantiza e cria o DataArray de cada tile
  for tile_year, tile_lon, tile_lat, _, crs, transform in tiles:
    tile_id = f"grid_{tile_lon:.2f}_{tile_lat:.2f}"
    base_path = (
        f"./global_0.1_degree_representation/{tile_year}/{tile_id}/{tile_id}"
    )

    quantized = np.load(f"{base_path}.npy")
    scales = np.load(f"{base_path}_scales.npy")

    emb = dequantize_embedding(quantized, scales)
    h, w, d = emb.shape

    cols = np.arange(w)
    rows = np.arange(h)

    # Coordenadas nativas dos eixos
    xs, _ = rasterio.transform.xy(
        transform, np.zeros_like(cols), cols, offset="center"
    )
    _, ys = rasterio.transform.xy(
        transform, rows, np.zeros_like(rows), offset="center"
    )

    # Criação do DataArray nativo
    da_tile = xr.DataArray(
        np.transpose(emb, (2, 0, 1)),
        dims=["band", "y", "x"],
        coords={"band": np.arange(d), "y": np.array(ys), "x": np.array(xs)},
    )
    da_tile.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
    da_tile.rio.write_crs(crs, inplace=True)
    da_tile.rio.write_transform(transform, inplace=True)

    # Reprojeta cada bloco individualmente para WGS84
    da_tile_wgs84 = da_tile.rio.reproject(WGS84_WKT)
    tile_arrays.append(da_tile_wgs84)

  # 3. Mescla os blocos já em WGS84
  if len(tile_arrays) > 1:
    da_mosaic = merge_arrays(tile_arrays)
  else:
    da_mosaic = tile_arrays[0]

  # 4. Recorta para o bounding box desejado
  minx, miny, maxx, maxy = bbox
  tessera_mosaic_embeddings = da_mosaic.rio.clip_box(
      minx=minx, miny=miny, maxx=maxx, maxy=maxy, crs=WGS84_WKT
  )

  return tessera_mosaic_embeddings

def harmonize_by_tile_embeddings(da: xr.DataArray, tile_corrections: list[dict]) -> xr.DataArray:
    """Corrige artefatos de média em múltiplos blocos preservando a ordem dos eixos (band, y, x).
    
    tile_corrections = [
        {"target": (-58.90, -2.60, -58.80, -2.50), "ref": (-58.98, -2.60, -58.90, -2.50)},
        {"target": (-58.80, -2.80, -58.70, -2.70), "ref": (-58.90, -2.80, -58.80, -2.70)},
    ]
    """
    da_curr = da.transpose("band", "y", "x").copy(deep=True)

    for corr in tile_corrections:
        minx, miny, maxx, maxy = corr["target"]
        rx0, ry0, rx1, ry1 = corr["ref"]

        # Fatiamento seguro de coordenadas
        y_slice_ref = slice(ry1, ry0) if da_curr.y[0] > da_curr.y[-1] else slice(ry0, ry1)
        x_slice_ref = slice(rx0, rx1) if da_curr.x[0] < da_curr.x[-1] else slice(rx1, rx0)
        
        y_slice_tgt = slice(maxy, miny) if da_curr.y[0] > da_curr.y[-1] else slice(miny, maxy)
        x_slice_tgt = slice(minx, maxx) if da_curr.x[0] < da_curr.x[-1] else slice(maxx, minx)

        # Vetores médios de 128 dimensões
        mean_ref = da_curr.sel(x=x_slice_ref, y=y_slice_ref).mean(dim=["x", "y"], skipna=True)
        mean_tgt = da_curr.sel(x=x_slice_tgt, y=y_slice_tgt).mean(dim=["x", "y"], skipna=True)
        delta = mean_ref - mean_tgt

        # Máscara espacial no grid (y, x)
        spatial_mask = (
            (da_curr.x >= minx) & (da_curr.x <= maxx) &
            (da_curr.y >= miny) & (da_curr.y <= maxy)
        )

        # Aplica o offset no bloco
        da_curr = xr.where(spatial_mask, da_curr + delta, da_curr)

    # Re-normalização L2 preservando a ordem dimensional
    norms = np.sqrt((da_curr ** 2).sum(dim="band"))
    norms = xr.where(norms == 0, 1.0, norms)
    
    da_aligned = (da_curr / norms).transpose("band", "y", "x")

    # Metadados espaciais
    da_aligned.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
    if da.rio.crs:
        da_aligned.rio.write_crs(da.rio.crs, inplace=True)
    if da.rio.transform():
        da_aligned.rio.write_transform(da.rio.transform(), inplace=True)
    da_aligned.rio.write_nodata(np.nan, inplace=True)

    return da_aligned

def validate_mosaic_pca(da):
    fig, axes = plt.subplots(1, min(da.shape[0], 4), figsize=(16, 4))
    for i, ax in enumerate(axes.ravel()):
        da.isel(band=i).plot.imshow(ax=ax, cmap="gray", robust=True)
        ax.set_title(f"Banda {i+1}")
    plt.tight_layout()
    plt.show()


def compute_pca_rgb(
    da: xr.DataArray, 
    n_components: int = 3, 
    p_min: float = 2.0, 
    p_max: float = 98.0
) -> xr.DataArray:
    """Aplica PCA em um DataArray raster e retorna um novo DataArray georreferenciado

    composto pelas componentes normalizadas em RGB [0.0, 1.0].
    """
    # 1. Garante que as dimensões estejam na ordem padronizada ("band", "y", "x")
    da_std = da.transpose("band", "y", "x")
    
    n_bands = da_std.sizes["band"]
    n_y = da_std.sizes["y"]
    n_x = da_std.sizes["x"]
    
    # 2. Achata para (N_pixels, N_bands)
    flat_data = da_std.values.transpose(1, 2, 0).reshape(-1, n_bands)

    # 3. Identifica pixels válidos (ignora NaNs e vetores zerados)
    valid_mask = ~np.isnan(flat_data).any(axis=1) & ~(flat_data == 0.0).all(axis=1)

    if not np.any(valid_mask):
        raise ValueError("O DataArray fornecido não contém dados válidos para ajuste do PCA.")

    # 4. Ajuste e transformação do PCA
    pca = PCA(n_components=n_components)
    transformed = pca.fit_transform(flat_data[valid_mask])

    # 5. Normalização Robusta por percentis
    p_low, p_high = np.percentile(transformed, (p_min, p_max), axis=0)
    diff = np.where((p_high - p_low) == 0, 1.0, (p_high - p_low))
    transformed_scaled = np.clip((transformed - p_low) / diff, 0.0, 1.0)

    # 6. Reconstrói a matriz preservando os NaNs nas bordas
    pca_result = np.full((n_y * n_x, n_components), np.nan, dtype=np.float32)
    pca_result[valid_mask] = transformed_scaled
    pca_raster = pca_result.reshape(n_y, n_x, n_components).transpose(2, 0, 1)

    # 7. Cria o novo DataArray georreferenciado
    da_pca = xr.DataArray(
        pca_raster,
        dims=["band", "y", "x"],
        coords={
            "band": list(range(1, n_components + 1)),
            "y": da_std.y,
            "x": da_std.x,
        },
        attrs={
            "description": f"PCA ({n_components} components) RGB Composite",
            "pca_explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        },
    )

    # 8. Herda metadados espaciais
    da_pca.rio.set_spatial_dims(x_dim="x", y_dim="y", inplace=True)
    if da_std.rio.crs is not None:
        da_pca.rio.write_crs(da_std.rio.crs, inplace=True)
    if da_std.rio.transform() is not None:
        da_pca.rio.write_transform(da_std.rio.transform(), inplace=True)
    da_pca.rio.write_nodata(np.nan, inplace=True)

    return da_pca

def extract_tessera_samples(
    tessera_mosaic: xr.DataArray,
    samples: gpd.GeoDataFrame,
    year: int,
    label_column: str = "label",
    all_touched: bool = True,
) -> pd.DataFrame:
  """Extrai os embeddings do mosaico Tessera (T0...TN) para amostras pontuais ou poligonais.

  Args:
      tessera_mosaic: DataArray do mosaico Tessera com dimensões (band, y, x).
      samples: GeoDataFrame contendo as amostras (Pontos ou Polígonos).
      year: Ano de referência das amostras.
      label_column: Nome da coluna de classe/label. Se None, busca
        automaticamente.
      all_touched: Considera pixels que tocam as bordas dos polígonos.

  Returns:
      pd.DataFrame: Tabela formatada com ['geometry', 'label', 'year', 'T0',
      ..., 'TN'].
  """
  # 1. Alinhamento de CRS
  gdf = samples.to_crs(tessera_mosaic.rio.crs)
  valid_mask_geom = gdf.geometry.is_valid & (~gdf.geometry.is_empty)
  gdf = gdf[valid_mask_geom].reset_index(drop=True)

  if gdf.empty:
    print("Nenhuma geometria válida encontrada.")
    return pd.DataFrame()

  n_bands = tessera_mosaic.shape[0]
  column_names = [f"T{i}" for i in range(n_bands)]

  # Identificação da coluna de rótulo
  if label_column is None:
    for col_candidate in ["class_multisource", "label", "class", "classe"]:
      if col_candidate in gdf.columns:
        label_column = col_candidate
        break
    if label_column is None:
      raise ValueError("Coluna de rótulo não encontrada no GeoDataFrame.")

  is_point = gdf.geometry.iloc[0].geom_type in ["Point", "MultiPoint"]

  if is_point:
    # --- FLUXO 1: AMOSTRAGEM DIRETA DE PONTOS (Nearest Neighbor) ---
    x_coords_da = xr.DataArray(gdf.geometry.x.values, dims="sample")
    y_coords_da = xr.DataArray(gdf.geometry.y.values, dims="sample")

    sampled = tessera_mosaic.sel(
        x=x_coords_da, y=y_coords_da, method="nearest"
    ).compute()

    # sampled shape: (band, sample) -> transpor para (sample, band)
    emb_values = sampled.values.T

    # Criação do GeoDataFrame de pontos
    df_embeddings = pd.DataFrame(emb_values, columns=column_names)
    df_embeddings["geometry"] = gdf.geometry.values
    df_embeddings["tile"] = gdf["tile"]
    df_embeddings["label"] = gdf[label_column].values
    df_embeddings["year"] = year

    gdf_joined = gpd.GeoDataFrame(
        df_embeddings, geometry="geometry", crs=tessera_mosaic.rio.crs
    )

  else:
    # --- FLUXO 2: RECORTE E EXTRAÇÃO DE POLÍGONOS ---
    da_clipped = tessera_mosaic.rio.clip(
        gdf.geometry.values,
        crs=tessera_mosaic.rio.crs,
        all_touched=all_touched,
        drop=True,
    )

    x_coords = da_clipped.x.values
    y_coords = da_clipped.y.values
    xx, yy = np.meshgrid(x_coords, y_coords)

    flat_embeddings = da_clipped.values.transpose(1, 2, 0).reshape(-1, n_bands)
    flat_lons = xx.ravel()
    flat_lats = yy.ravel()

    # Remove pixels nulos/fora dos polígonos
    valid_mask = ~np.isnan(flat_embeddings).any(axis=1)
    valid_embeddings = flat_embeddings[valid_mask]
    valid_lons = flat_lons[valid_mask]
    valid_lats = flat_lats[valid_mask]

    if len(valid_embeddings) == 0:
      print("Nenhum pixel válido interceptou os polígonos.")
      return pd.DataFrame()

    df_embeddings = pd.DataFrame(valid_embeddings, columns=column_names)
    points = [Point(x, y) for x, y in zip(valid_lons, valid_lats)]
    gdf_pixels = gpd.GeoDataFrame(
        df_embeddings, geometry=points, crs=tessera_mosaic.rio.crs
    )

    gdf_joined = gpd.sjoin(
        gdf_pixels,
        gdf,
        how="inner",
        predicate="intersects",
    )
    gdf_joined["label"] = gdf_joined[label_column]
    gdf_joined["year"] = year

  # 3. Formatação final em WKT e ordenação das colunas
  gdf_joined["geometry"] = gdf_joined.geometry.to_wkt()
  final_cols = ["geometry", "tile", "label", "year"] + column_names

  df_final = (
      pd.DataFrame(gdf_joined[final_cols])
      .drop_duplicates(subset=["geometry"])
      .reset_index(drop=True)
  )

  print(f"Total de amostras Tessera extraídas: {len(df_final)}")
  return df_final

def generatePlotFigPatterns(data, label, smoothing = False, window_length = 7, polyorder = 2):
    only_values = data
    # Statistics
    mean_values = only_values.mean(axis=0)
    median_values = only_values.median(axis=0)
    q1 = only_values.quantile(0.25, axis=0)
    q3 = only_values.quantile(0.75, axis=0)

    if smoothing:
        mean_values = savgol_filter(mean_values, window_length=window_length, polyorder=polyorder)
        median_values = savgol_filter(median_values, window_length=window_length, polyorder=polyorder)
        q1 = savgol_filter(q1, window_length=window_length, polyorder=polyorder)
        q3 = savgol_filter(q3, window_length=window_length, polyorder=polyorder)
        
    # Dates
    indexes = data.columns
    # Plot
    fig, ax = plt.subplots(figsize=(18, 5))
    # Mean curve
    ax.plot(
        indexes,
        mean_values,
        marker="o",
        linewidth=2,
        label="Mean"
    )
    # Median curve
    ax.plot(
        indexes,
        median_values,
        linestyle="--",
        linewidth=2,
        label="Median"
    )
    # Quartile interval
    ax.fill_between(
        indexes,
        q1,
        q3,
        alpha=0.2,
        label="Q1-Q3"
    )
    fig.subplots_adjust(left = 0.06)
    ax.set_title(f"{label} Embeddings")
    ax.set_xlabel("Embeddings")
    ax.legend()
    plt.xticks(range(0, len(mean_values), int(len(mean_values) / 8)))
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_embeddings_rgb_folium(
    da: xr.DataArray,
    band_indices: list[int] = (10, 35, 70),
    p_min: float = 2.0,
    p_max: float = 98.0,
    zoom_start: int = 12,
    title: str = f"Tessera Plot Emb",
    tiles: str = "OpenStreetMap",
) -> folium.Map:
    """Seleciona 3 bandas de um DataArray de embeddings (128, H, W),

    normaliza em RGB com canal Alpha transparente e retorna um mapa Folium.
    """
    if len(band_indices) != 3:
        raise ValueError(
            "O parâmetro 'band_indices' deve conter exatamente 3 índices."
        )

    # 1. Seleciona as 3 bandas e reordena para (H, W, 3)
    da_subset = da.isel(band=list(band_indices))
    img_data = da_subset.values.transpose(1, 2, 0)

    # 2. Identifica os pixels válidos (sem NaNs e não zerados)
    valid_mask = ~np.isnan(img_data).any(axis=-1) & ~(img_data == 0.0).all(
        axis=-1
    )

    if not np.any(valid_mask):
        raise ValueError(
            "Nenhum pixel válido encontrado nas bandas selecionadas."
        )

    # 3. Normalização robusta independente por canal
    clean_pixels = img_data[valid_mask]
    p_low, p_high = np.percentile(clean_pixels, (p_min, p_max), axis=0)
    diff = np.where((p_high - p_low) == 0, 1.0, (p_high - p_low))

    img_scaled = np.clip((img_data - p_low) / diff, 0.0, 1.0) * 255.0
    rgb_uint8 = np.nan_to_num(img_scaled, nan=0.0).astype(np.uint8)

    # 4. Canal Alpha para manter bordas e NaNs transparentes
    alpha = (valid_mask * 255).astype(np.uint8)[:, :, np.newaxis]
    rgba_img = np.concatenate([rgb_uint8, alpha], axis=-1)

    # 5. Configuração espacial dos bounds
    minx, miny, maxx, maxy = da_subset.rio.bounds()
    bounds = [[miny, minx], [maxy, maxx]]
    center = [(miny + maxy) / 2, (minx + maxx) / 2]

    # 6. Renderização no Folium
    m = folium.Map(location=center, zoom_start=zoom_start, tiles=tiles)

    band_indices_str = "-".join(map(str, band_indices))
    return folium.raster_layers.ImageOverlay(
        name=title,
        image=rgba_img,
        bounds=bounds,
        opacity=1.0,
        interactive=True,
        zindex=1,
    )

def plot_pca_rgb_folium(
    da_pca_rgb: xr.DataArray,
    zoom_start: int = 12,
    title: str = f"Tessera Plot RGB PCA",
    tiles: str = "OpenStreetMap",
) -> folium.Map:
    """Recebe um DataArray com o PCA-RGB (3, H, W) e retorna um mapa Folium

    com canal Alpha transparente para bordas e NaNs.
    """
    # 1. Converte (3, H, W) -> (H, W, 3)
    rgb_data = da_pca_rgb.values.transpose(1, 2, 0)

    # 2. Identifica os pixels válidos (sem NaNs e não zerados)
    valid_mask = ~np.isnan(rgb_data).any(axis=-1) & ~(rgb_data == 0.0).all(
        axis=-1
    )

    if not np.any(valid_mask):
        raise ValueError("O DataArray não contém pixels válidos para exibição.")

    # 3. Converte float [0, 1] para uint8 [0, 255]
    rgb_uint8 = np.nan_to_num(rgb_data, nan=0.0)
    rgb_uint8 = np.clip(rgb_uint8 * 255.0, 0, 255).astype(np.uint8)

    # 4. Cria o canal Alpha: 0 (transparente) e 255 (opaco)
    alpha = (valid_mask * 255).astype(np.uint8)[:, :, np.newaxis]
    rgba_img = np.concatenate([rgb_uint8, alpha], axis=-1)

    # 5. Obtém limites e centro para o Folium
    minx, miny, maxx, maxy = da_pca_rgb.rio.bounds()
    bounds = [[miny, minx], [maxy, maxx]]
    center = [(miny + maxy) / 2, (minx + maxx) / 2]

    # 6. Cria o mapa e adiciona o overlay
    m = folium.Map(location=center, zoom_start=zoom_start, tiles=tiles)

    return folium.raster_layers.ImageOverlay(
        name=title,
        image=rgba_img,
        bounds=bounds,
        opacity=1.0,
        interactive=True,
        zindex=1,
    )