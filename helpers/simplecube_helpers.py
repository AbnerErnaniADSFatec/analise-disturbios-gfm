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
from pyproj import Transformer
from rasterio.features import rasterize
from rasterio.transform import Affine
from scipy.signal import savgol_filter
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, RobustScaler

from helpers.simplecube import load_xarray, save_xarray, simple_cube

STAC_URL = "https://data.inpe.br/bdc/stac/v1"
WTSS_URL = "https://data.inpe.br/bdc/wtss/v4/"

WGS84_WKT = (
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
    'AUTHORITY["EPSG","4326"]]'
)

def format_bbox(bbox_string):
    return ",".join(map(str, bbox_string))

def get_center(gdf):
    min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
    return [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2] 

def get_composition(cube_id, reject: any = []):
    service = pystac_client.Client.open(STAC_URL)
    collection = service.get_collection(cube_id)
    item_assets = collection.to_dict()['item_assets']
    composition = [ id for id in list(item_assets.keys()) if id not in reject]
    return composition

def rgb_cube_norm(cube, time_idx = 0):
    r, g, b = ['red', 'green', 'blue']
    if time_idx == 0:
        rgb_composition = xr.concat([cube[var].isel(band=0) for var in [r, g, b]], dim="band")
    else:
        rgb_composition = xr.concat([cube[var].isel(time=time_idx, band=0) for var in [r, g, b]], dim="band")
    rgb_composition = rgb_composition.assign_coords(band=["R", "G", "B"])
    rgb_composition = rgb_composition.transpose("y", "x", "band")
    rgb_composition = rgb_composition / rgb_composition.max() # normalize
    raw_vals = np.nan_to_num(rgb_composition.values, nan=0.0)
    return (np.clip(raw_vals, 0.0, 1.0) * 255).astype(np.uint8)

def get_bounds_tile(tile):
    min_lon, min_lat, max_lon, max_lat = tile.to_crs(epsg=4326).total_bounds
    return [[min_lat, min_lon], [max_lat, max_lon]]

def get_bounds_cube(cube_):
    min_lon, min_lat, max_lon, max_lat = cube_.rio.bounds()
    return [[min_lat, min_lon], [max_lat, max_lon]]

def get_ts(sample):
    item = sample['time_series']
    ts_ = item if isinstance(sample, dict) else eval(item)
    return pd.DataFrame(ts_)

def make_request_wtss(coverage, bands, start, end, longitude, latitude):
    bands = ",".join(bands)
    url = (f"{urllib.parse.urljoin(WTSS_URL, f'time_series')}?" +
          f"coverage={coverage}" +
          f"&attributes={bands}" +
          f"&start_date={start}" +
          f"&end_date={end}" +
          f"&latitude={latitude}" +
          f"&longitude={longitude}")
    response = requests.get(url).json().get('result', None)
    if response:
        ts_ = {'Index': response['timeline']}
        band_values = response['attributes']
        for data_ in band_values:
            ts_[data_['attribute']] = data_['values']
        return(json.dumps(ts_))
    else:
        return(json.dumps({}, ensure_ascii=False))

def sample_points_in_polygons(gdf, n_points_per_polygon = 1, top_n = 1, class_column = "label"):
    points = []
    class_ = []

    for _, row in gdf.iterrows():
        geom = row.geometry

        # se for multipolygon, ele identifica os top_n maiores
        if isinstance(geom, MultiPolygon):
            polygons = list(geom.geoms)

            # ordenar por área (maior → menor)
            polygons = sorted(polygons, key=lambda p: p.area, reverse=True)

            # pegar os top N maiores
            polygons = polygons[:top_n]
        else:
            polygons = [geom]

        # Amostrar aleatóriamente em cada polígono selecionado
        for poly in polygons:
            minx, miny, maxx, maxy = poly.bounds
            count = 0

            while count < n_points_per_polygon:
                x = np.random.uniform(minx, maxx)
                y = np.random.uniform(miny, maxy)
                p = Point(x, y)

                if poly.contains(p):
                    points.append(p)
                    class_.append(row[class_column])
                    count += 1

    return gpd.GeoDataFrame({'label': class_}, geometry=points, crs=gdf.crs)

def plot_xarray_(
    data,
    bands=None,
    title=None,
    figsize=(9, 8),
    p_min=2,
    p_max=98,
):
  """Plota qualquer xarray.DataArray ou xarray.Dataset de 3 bandas/variáveis

  preservando o CRS e o georreferenciamento nativo.

  Args:
      data: xr.DataArray (shape com 3 bandas) ou xr.Dataset (com 3 variáveis).
      bands: Lista com o nome/índice das 3 bandas (opcional).
      title: Título do gráfico (opcional).
      figsize: Tamanho da figura do matplotlib.
      p_min: Percentil mínimo para stretch de contraste (padrão: 2).
      p_max: Percentil máximo para stretch de contraste (padrão: 98).
  """
  # 1. Se for Dataset, converte para DataArray concatenando as variáveis
  if isinstance(data, xr.Dataset):
    if bands is not None:
      var_list = bands
    else:
      var_list = list(data.data_vars.keys())[:3]
    if len(var_list) < 3:
      raise ValueError(f"O Dataset precisa de 3 variáveis. Encontradas: {var_list}")
    da = xr.concat([data[v] for v in var_list], dim="band")
    da = da.assign_coords(band=var_list)
  elif isinstance(data, xr.DataArray):
    da = data.copy()
    if bands is not None:
      # Filtra pelas bandas solicitadas
      channel_dim = [
          d
          for d in da.dims
          if d.lower() in ["band", "bands", "channel", "channels", "variable"]
      ]
      dim_name = channel_dim[0] if channel_dim else da.dims[0]
      da = da.sel({dim_name: bands})
  else:
    raise TypeError("O objeto deve ser um xarray.DataArray ou xarray.Dataset.")

  # 2. Identifica dimensões espaciais (x/y ou lon/lat)
  spatial_x = next(
      (d for d in da.dims if d.lower() in ["x", "lon", "longitude"]), None
  )
  spatial_y = next(
      (d for d in da.dims if d.lower() in ["y", "lat", "latitude"]), None
  )
  channel_dim = next(
      (
          d
          for d in da.dims
          if d.lower()
          in ["band", "bands", "channel", "channels", "variable", "dim_0"]
      ),
      None,
  )

  if not spatial_x or not spatial_y:
    raise ValueError(
        f"Não foi possível identificar dimensões espaciais em: {da.dims}"
    )

  # Se a dimensão de cor não foi nomeada, assume a restante
  if not channel_dim:
    remaining = [d for d in da.dims if d not in [spatial_x, spatial_y]]
    if remaining:
      channel_dim = remaining[0]
    else:
      raise ValueError("O DataArray precisa de uma terceira dimensão com 3 bandas.")

  # Garante que possui exatamente 3 canais
  if da.sizes[channel_dim] != 3:
    raise ValueError(
        f"A dimensão '{channel_dim}' precisa ter tamanho 3, mas tem {da.sizes[channel_dim]}."
    )

  # 3. Normalização por percentil por canal
  norm_arrays = []
  for i in range(3):
    band_slice = da.isel({channel_dim: i})
    vals = band_slice.values
    valid_vals = vals[~np.isnan(vals)]
    
    if len(valid_vals) > 0:
      p_low, p_high = np.nanpercentile(valid_vals, (p_min, p_max))
      band_norm = np.clip((band_slice - p_low) / (p_high - p_low + 1e-6), 0, 1)
    else:
      band_norm = xr.zeros_like(band_slice)
      
    norm_arrays.append(band_norm)

  da_norm = xr.concat(norm_arrays, dim=channel_dim)

  # 4. Plota com o spatial ref
  fig, ax = plt.subplots(figsize=figsize)
  da_norm.plot.imshow(
      x=spatial_x,
      y=spatial_y,
      rgb=channel_dim,
      robust=False,
      ax=ax,
  )

  crs_label = da.rio.crs if hasattr(da, "rio") and da.rio.crs else "Não definido"
  ax.set_title(title or f"Composição RGB")
  ax.ticklabel_format(useOffset=False, style="plain")
  plt.tight_layout()
  plt.grid(False)
  plt.show()

def normalize_rgb(cube):
    # 1. Cria uma cópia do cubo para preservar os dados originais das outras bandas
    cube_norm = cube.copy()
    
    # 2. Normaliza apenas as bandas RGB por percentil (desconsiderando zeros e NaNs)
    rgb_bands = ["red", "green", "blue"]
    
    for band in rgb_bands:
      if band in cube_norm.data_vars:
        vals = cube_norm[band].values
        # Máscara de pixels válidos (ignora NoData e bordas pretas)
        valid_mask = (~np.isnan(vals)) & (vals > 0)
    
        if valid_mask.any():
          p2, p98 = np.percentile(vals[valid_mask], (2, 98))
          if p98 == p2:
            p98 = p2 + 1e-6
    
          norm_vals = np.clip((vals - p2) / (p98 - p2), 0, 1)
          norm_vals[~valid_mask] = 0.0
    
          cube_norm[band].values = norm_vals
    return cube_norm

def extract_sits_samples(
    cube: xr.Dataset,
    samples_gdf: gpd.GeoDataFrame,
    label_col: str,
    year: int,
    cube_id: str = "sentinel2_cube",
    all_touched: bool = True,
) -> pd.DataFrame:
  """Extrai séries temporais de amostras pontuais ou poligonais

  no formato tabular do pacote sits.
  """
  # 1. Alinhamento de CRS e preparação do cubo
  ds_crs = cube.rio.crs
  samples_proj = samples_gdf.to_crs(ds_crs)
  cube_clean = cube.squeeze("band", drop=True) if "band" in cube.dims else cube

  # 2. Filtragem de geometrias válidas
  valid_mask = samples_proj.geometry.is_valid & (
      ~samples_proj.geometry.is_empty
  )
  samples_proj = samples_proj[valid_mask].reset_index(drop=True)

  if samples_proj.empty:
    print("Nenhuma geometria válida encontrada.")
    return pd.DataFrame()

  # Detecta o tipo geométrico principal da camada
  is_point = samples_proj.geometry.iloc[0].geom_type in ["Point", "MultiPoint"]

  # 3. Extração das coordenadas dependendo do tipo de geometria
  if is_point:
    # --- FLUXO PARA PONTOS ---
    x_vals = samples_proj.geometry.x.values
    y_vals = samples_proj.geometry.y.values
    poly_indices = np.arange(len(samples_proj))

    # Amostragem usando vizinho mais próximo na grade
    x_coords_da = xr.DataArray(x_vals, dims="pixel")
    y_coords_da = xr.DataArray(y_vals, dims="pixel")
    sampled_pixels = cube_clean.sel(
        x=x_coords_da, y=y_coords_da, method="nearest"
    ).compute()

  else:
    # --- FLUXO PARA POLÍGONOS (Rasterização) ---
    geom_value_pairs = [
        (geom, idx) for idx, geom in enumerate(samples_proj.geometry)
    ]
    transform = cube_clean.rio.transform()
    shape = (cube_clean.y.size, cube_clean.x.size)

    mask_poly_idx = rasterize(
        shapes=geom_value_pairs,
        out_shape=shape,
        transform=transform,
        fill=-1,
        all_touched=all_touched,
        dtype=np.int32,
    )

    y_indices, x_indices = np.where(mask_poly_idx != -1)

    if len(x_indices) == 0:
      print("Nenhum pixel do cubo interceptou os polígonos fornecidos.")
      return pd.DataFrame()

    poly_indices = mask_poly_idx[y_indices, x_indices]
    x_vals = cube_clean.x.values[x_indices]
    y_vals = cube_clean.y.values[y_indices]

    x_coords_da = xr.DataArray(x_vals, dims="pixel")
    y_coords_da = xr.DataArray(y_vals, dims="pixel")
    sampled_pixels = cube_clean.sel(x=x_coords_da, y=y_coords_da).compute()

  # 4. Conversão das coordenadas para WGS84 (Graus)
  transformer = Transformer.from_crs(ds_crs, "EPSG:4326", always_xy=True)
  pixel_lons, pixel_lats = transformer.transform(x_vals, y_vals)

  # 5. Formatação das datas de 16 em 16 dias do BDC
  base_date = pd.to_datetime(f"{year}-01-01")
  formatted_dates = [
      (base_date + pd.Timedelta(days=int(d))).strftime("%Y-%m-%d")
      for d in cube_clean.time.values
  ]

  # 6. Construção do DataFrame tabular do sits
  band_names = list(cube_clean.data_vars.keys())
  records = []

  for pix_i in range(len(x_vals)):
    p_idx = poly_indices[pix_i]
    row = samples_proj.iloc[p_idx]

    sample_series = {"Index": formatted_dates}
    for b in band_names:
      sample_series[b] = sampled_pixels[b].isel(pixel=pix_i).values.tolist()

    records.append({
        "longitude": pixel_lons[pix_i],
        "latitude": pixel_lats[pix_i],
        "label": row[label_col],
        "start_date": formatted_dates[0],
        "end_date": formatted_dates[-1],
        "cube": cube_id,
        "time_series": str(sample_series),
    })

  df_sits = pd.DataFrame(records)
  print(f"Total de amostras/pixels extraídos: {len(df_sits)}")
  return df_sits



def plot_ts(data_df, selected_line, marker=True, smoothed=False, step=5):
    ts = pd.DataFrame(json.loads(data_df['time_series'][selected_line]))
    fig = plt.figure(figsize=(10, 4))
    smoothed_ = ' Smoothed' if smoothed else ''
    fig.suptitle(
        ("{cube} {label} [{lng:,.4f}, {lat:,.4f}]{smoothed_} WGS 84 EPSG:4326").format(
            cube=data_df['cube'][selected_line],
            label=data_df['label'][selected_line],
            lng=data_df['longitude'][selected_line],
            lat=data_df['latitude'][selected_line],
            smoothed_=smoothed_
        )
    )
    seaborn.set_theme(style="darkgrid")
    bands = [band for band in list(ts.keys()) if band != 'Index']
    marker_ = 'o' if marker else None
    for band in bands:
        seaborn.lineplot(
            data=ts,
            x="Index",
            y=band,
            label=band,
            markersize=8,
            marker=marker_,
            linestyle='-'
        )
    ax = plt.gca()
    xticks = range(0, len(ts["Index"]), step)
    ax.set_xticks(xticks)
    ax.set_xticklabels(
        ts["Index"].iloc[::step]
    )
    plt.xlabel(None)
    plt.ylabel(None)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_patterns(samples, band, step=3):
    labels = sorted(samples["label"].unique())

    for label in labels:
        samples_label = samples[samples["label"] == label][
            "time_series"
        ].reset_index(drop=True)

        if len(samples_label) == 0:
            continue

        all_values = []
        date_index = None

        # Lê todas as amostras
        for item in samples_label:
            # Se for string converte, se já for dicionário usa direto
            sample_dict = item if isinstance(item, dict) else eval(item)
            df = pd.DataFrame(sample_dict)

            # Salva o índice de datas da primeira amostra válida
            if date_index is None:
                date_index = pd.to_datetime(df["Index"])

            # Extração da banda
            all_values.append(df[band])

        # Cria matriz: (rows = samples, cols = timesteps)
        only_values = pd.DataFrame(all_values)

        # Estatísticas
        mean_values = only_values.mean(axis=0)
        median_values = only_values.median(axis=0)
        q1 = only_values.quantile(0.25, axis=0)
        q3 = only_values.quantile(0.75, axis=0)

        # Plot
        fig, ax = plt.subplots(figsize=(12, 5))

        # Curva da Média
        ax.plot(
            date_index, mean_values, marker="o", linewidth=2, label="Mean"
        )

        # Curva da Mediana
        ax.plot(
            date_index,
            median_values,
            linestyle="--",
            linewidth=2,
            label="Median",
        )

        # Intervalo interquartil (Q1 - Q3)
        ax.fill_between(
            date_index, q1, q3, alpha=0.2, label="Q1-Q3 (Percentiles 25-75)"
        )

        # Configurações do gráfico
        ax.set_title(f"{label} Time Series Patterns ({band.upper()})")
        ax.set_xlabel("Date")
        ax.set_ylabel(band.upper())
        ax.grid(True, linestyle=":", alpha=0.6)

        # Formatação do eixo de datas
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=step))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()

        ax.legend()
        plt.tight_layout()
        plt.show()

def extract_bands_ts(samples, line, bands_to_select):
    # Se for string converte, se já for dicionário usa direto
    item = samples['time_series'][line]
    sample_dict = item if isinstance(item, dict) else eval(item)
    ts_ = pd.DataFrame(sample_dict)
    bands_ = ["Index"] + bands_to_select
    ts_ = ts_[bands_]
    return ts_

def extract_bands(samples, bands):
    samples_ = samples.copy()
    for row in range(0, len(samples_)):
        samples_.loc[row, 'time_series'] = json.dumps(extract_bands_ts(samples_, row, bands).to_dict(orient="list"))
    return samples_

def get_band_description(band, bands_description, key: str = "common_name"):
    selected = {}
    for band_desc in bands_description:
        if band_desc[key] == band:
            selected = band_desc
            break
    return selected
    
def normalize_ts(samples, line, bands_description):
    item = samples['time_series'][line]
    sample_dict = item if isinstance(item, dict) else eval(item)
    ts_ = pd.DataFrame(sample_dict)
    for column in ts_.columns:
        if column != "Index":
            band_desc = get_band_description(column, bands_description)
            if band_desc:
                scale = band_desc['scale']
                ts_[column] = ts_[column] * scale
    return ts_

def normalize_(samples, bands_description):
    samples_ = samples.copy()
    for row in range(0, len(samples_)):
        samples_.loc[row, 'time_series'] = json.dumps(normalize_ts(samples_, row, bands_description).to_dict(orient="list"))
    return samples_

def _set_NaN(value, missing_value):
    if value != missing_value:
        return value
    else:
        return None
    
def std_(X_):
    std = X_.std(axis=0)
    std[std == 0] = 1
    return std

def interpolate_ts(samples, line, bands_description):
    item = samples['time_series'][line]
    sample_dict = item if isinstance(item, dict) else eval(item)
    ts_ = pd.DataFrame(sample_dict)
    for column in ts_.columns:
        if column != "Index":
            band_desc = get_band_description(column, bands_description)
            if band_desc:
                scale = band_desc['scale']
                missing_value = band_desc['nodata'] * scale
                ts_[column] = ts_[column].apply(lambda x: _set_NaN(x, missing_value)).interpolate(
                    method = 'linear',
                    limit_direction = 'forward',
                    order = 2
                )
    return ts_

def interpolate_single_ts(ts_, bands_description):
    for column in ts_.columns:
        if column != "Index":
            band_desc = get_band_description(column, bands_description)
            scale = band_desc['scale']
            missing_value = band_desc['nodata'] * scale
            ts_[column] = ts_[column].apply(lambda x: _set_NaN(x, missing_value)).interpolate(
                method = 'linear',
                limit_direction = 'forward',
                order = 2
            )
    return ts_

def interpolate_(samples, bands_description):
    samples_ = samples.copy()
    for row in range(0, len(samples_)):
        samples_.loc[row, 'time_series'] = json.dumps(interpolate_ts(samples_, row, bands_description).to_dict(orient="list"))
    return samples_

class SGolay:
    def __init__(self, window_size: int, polynomial_order: int, mode: str = "interp"):
        self.mode = mode
        if (window_size % 2) != 0:
            self.window_size = window_size
        else:
            raise Exception("Window size must be odd number!")
        if window_size > polynomial_order:
            self.polynomial_order = polynomial_order
        else:
            raise Exception("Window size must be higher than the polynomial order!")

    def apply(self, samples, line):
        item = samples['time_series'][line]
        sample_dict = item if isinstance(item, dict) else eval(item)
        ts_ = pd.DataFrame(sample_dict)
        return self.apply_ts(ts_)

    def apply_ts(self, ts_):
        for column in ts_.columns:
            if column != "Index":
                ts_[column] = savgol_filter(
                    ts_[column],
                    window_length=self.window_size,
                    polyorder=self.polynomial_order,
                    mode=self.mode
                )
        return ts_

def smooth_(samples, sgolay):
    samples_ = samples.copy()
    for row in range(0, len(samples_)):
        samples_.loc[row, 'time_series'] = json.dumps(sgolay.apply(samples_, row).to_dict(orient="list"))
    return samples_