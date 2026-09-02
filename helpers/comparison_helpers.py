import json
import random
import re

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shapely
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial import cKDTree
from shapely import wkt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

def read_gdf(file):
    samples = pd.read_csv(file)
    if "geometry" in samples.keys():
        samples["geometry"] = samples["geometry"].apply(wkt.loads)
    else:
        samples["geometry"] = gpd.points_from_xy(samples["longitude"], samples["latitude"])
        samples = samples.drop(columns = ["longitude", "latitude"])
    return gpd.GeoDataFrame(samples, geometry="geometry", crs="EPSG:4326")

def check_gdfs(gdfs, names):
    for name, gdf in zip(names, gdfs):
        print(f"=== {name} ===")
        print(f"Linhas: {len(gdf)}")
        print(f"CRS declarado: {gdf.crs}")
        if not gdf.empty:
            p = gdf.geometry.dropna().iloc[0]
            print(f"Exemplo Geom: POINT ({p.x:.6f}, {p.y:.6f})")
            print(f"Bounding Box: {gdf.total_bounds}")
        print()

def find_commom_geoms_nearest(lista_gdfs: list[gpd.GeoDataFrame], max_distance_meters: float = 30.0) -> list[gpd.GeoDataFrame]:
    """
    Pareia pontos entre múltiplos GeoDataFrames com base em proximidade espacial (metros).
    Retorna a mesma lista ordenada com as linhas exatamente alinhadas 1-para-1.
    """
    if not lista_gdfs:
        return []

    crs_metrico = "EPSG:3857"
    
    # 1. Padroniza projeção e reseta índice mantendo rastreabilidade
    gdfs_norm = [
        gdf.to_crs(crs_metrico).reset_index(drop=True) 
        for gdf in lista_gdfs
    ]
    
    # 2. Inicia o pareamento com o primeiro GeoDataFrame
    df_pares = gpd.GeoDataFrame({"idx_0": gdfs_norm[0].index, "geometry": gdfs_norm[0].geometry}, crs=crs_metrico)

    for i in range(1, len(gdfs_norm)):
        target = gdfs_norm[i][["geometry"]]
        
        # Faz a busca do vizinho mais próximo dentro da tolerância
        joined = gpd.sjoin_nearest(
            df_pares,
            target,
            how="inner",
            max_distance=max_distance_meters
        )
        
        # A coluna 'index_right' contém o índice da linha correspondente em gdfs_norm[i]
        joined = joined.rename(columns={"index_right": f"idx_{i}"})
        
        # Garante relação 1-para-1 (remove múltiplos pontos mapeados para o mesmo pixel)
        joined = joined.drop_duplicates(subset=["idx_0"]).drop_duplicates(subset=[f"idx_{i}"])
        
        df_pares = joined

    if df_pares.empty:
        print("Aviso: Nenhum ponto encontrado em comum dentro da tolerância especificada.")
        return [gdf.iloc[0:0].copy() for gdf in lista_gdfs]

    # 3. Filtra e alinha cada GeoDataFrame original com os índices pareados
    resultado = []
    for i, gdf_orig in enumerate(lista_gdfs):
        indices_alinhados = df_pares[f"idx_{i}"].values
        # Usa iloc para garantir que a linha n do DataFrame 0 bata com a linha n dos outros
        filtrado = gdf_orig.iloc[indices_alinhados].copy().reset_index(drop=True)
        resultado.append(filtrado)

    return resultado

def plot_balance(
    df,
    class_column,
    title="Distribuição das Classes",
    colors_by_class: dict | list = None,
):
    """Plota a distribuição de classes em um gráfico de pizza com suporte a cores customizadas.

    :param df: DataFrame ou GeoDataFrame contendo os dados.
    :param class_column: Nome da coluna que define as classes (ex: 'label').
    :param title: Título do gráfico.
    :param colors_by_class: Dicionário mapeando {classe: cor} (ex: {'Forest':
        '#2ecc71', ...}) ou lista de cores. Se None, usa a paleta Set2.
    """
    class_counts = df[class_column].value_counts()

    # Mapeia as cores conforme a ordem das fatias (class_counts.index)
    if isinstance(colors_by_class, dict):
        # Garante fallback de cor cinza caso alguma classe não esteja no dicionário
        pie_colors = [
            colors_by_class.get(cls, "#95a5a6") for cls in class_counts.index
        ]
    elif isinstance(colors_by_class, list):
        pie_colors = [
            colors_by_class[i % len(colors_by_class)]
            for i in range(len(class_counts))
        ]
    else:
        pie_colors = plt.cm.Set2.colors

    plt.figure(figsize=(8, 8))

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f"{pct:.1f}%\n({val:,})"

        return my_autopct

    plt.pie(
        class_counts.values,
        labels=class_counts.index,
        autopct=make_autopct(class_counts.values),
        startangle=140,
        colors=pie_colors,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )

    plt.title(title, fontsize=14, pad=20, fontweight="bold")
    plt.tight_layout()
    plt.show()

def generatePlotFigPatternsAlphaEarth(data, label, smoothing = False, window_length = 7, polyorder = 2):
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
    plt.xticks(range(0, 64, 4))
    plt.ylim(-0.4, 0.4)
    plt.grid(True, alpha=0.3)
    plt.show()

def generatePlotFigPatternsTessera(data, label, smoothing = False, window_length = 7, polyorder = 2):
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

def plot_heatmap(
    df_emb,
    df_sentinel,
    embedding_type="alphaearth",
    agg_method="mean",
    label_col=None,
    roi_name = ""
):
    """Gera mapas de calor da correlação de Pearson entre Embeddings (AlphaEarth ou Tessera)
    e Séries Temporais do Sentinel-2, com suporte a agregação temporal e divisão por classes.

    :param df_emb: GeoDataFrame/DataFrame com a coluna 'geometry' e colunas de embedding.
    :param df_sentinel: GeoDataFrame/DataFrame com a coluna 'geometry' e a 'time_series' (JSON).
    :param embedding_type: 'alphaearth' (64 dims) ou 'tessera' (128 dims).
    :param agg_method: 'mean', 'median', 'std' ou um int (sample_idx).
    :param label_col: Nome da coluna de classes em df_emb (ex: 'label'). Se None, plota geral.
    """
    if roi_name:
        roi_name = f" ({roi_name}) "
    df_emb_proc = df_emb.copy().reset_index(drop=True)
    df_sent_proc = df_sentinel.copy().reset_index(drop=True)

    # 1. Configuração do tipo de embedding (AlphaEarth vs Tessera)
    emb_key = embedding_type.lower()
    if emb_key == "alphaearth":
        nome_modelo = "AlphaEarth"
        emb_cols = [f"A{i:02d}" for i in range(64)]
        fig_width = 18
    elif emb_key == "tessera":
        nome_modelo = "Tessera"
        # Detecta se as colunas estão no padrão T0..T127 ou T00..T127
        if "T0" in df_emb_proc.columns:
            emb_cols = [f"T{i}" for i in range(128)]
        elif "T00" in df_emb_proc.columns:
            emb_cols = [f"T{i:02d}" for i in range(128)]
        else:
            # Fallback: pega todas as colunas que começam com 'T' seguidas de número
            emb_cols = [
                c for c in df_emb_proc.columns if c.startswith("T") and c[1:].isdigit()
            ][:128]
        fig_width = 24  # Maior largura para comportar 128 dimensões
    else:
        raise ValueError("embedding_type deve ser 'alphaearth' ou 'tessera'.")

    # Garante que as colunas existam no DataFrame
    colunas_faltantes = [c for c in emb_cols if c not in df_emb_proc.columns]
    if colunas_faltantes:
        raise KeyError(
            f"Colunas de embedding não encontradas no DataFrame: {colunas_faltantes[:5]}... (Total: {len(colunas_faltantes)})"
        )

    # 2. Extração direta de coordenadas via shapely
    def extrair_coords(series_geom):
        geoms = series_geom.apply(
            lambda g: shapely.wkt.loads(g) if isinstance(g, str) else g
        ).values
        return np.column_stack((shapely.get_x(geoms), shapely.get_y(geoms)))

    coords_emb = extrair_coords(df_emb_proc["geometry"])
    coords_sentinel = extrair_coords(df_sent_proc["geometry"])

    # 3. Alinhamento espacial via KDTree
    tree = cKDTree(coords_sentinel)
    _, nearest_indices = tree.query(coords_emb)

    matched_ts = [
        json.loads(df_sent_proc.iloc[idx]["time_series"])
        if isinstance(df_sent_proc.iloc[idx]["time_series"], str)
        else df_sent_proc.iloc[idx]["time_series"]
        for idx in nearest_indices
    ]
    bands = [k for k in matched_ts[0].keys() if k != "Index"]

    # 4. Agregação temporal das bandas Sentinel-2
    band_values = {}
    nome_metodo = ""

    if isinstance(agg_method, str):
        agg = agg_method.lower()
        if agg not in ["mean", "median", "std"]:
            raise ValueError(
                "agg_method deve ser 'mean', 'median', 'std' ou um int (sample_idx)."
            )

        nome_metodo = {
            "mean": "Média Temporal",
            "median": "Mediana Temporal",
            "std": "Desvio Padrão Temporal",
        }[agg]

        for band in bands:
            serie_matriz = np.array(
                [[float(v) for v in ts[band]] for ts in matched_ts]
            )
            if agg == "mean":
                band_values[band] = np.nanmean(serie_matriz, axis=1)
            elif agg == "median":
                band_values[band] = np.nanmedian(serie_matriz, axis=1)
            elif agg == "std":
                band_values[band] = np.nanstd(serie_matriz, axis=1)

    elif isinstance(agg_method, int):
        num_dates = len(matched_ts[0]["Index"])
        sample_idx = agg_method % num_dates
        selected_date = matched_ts[0]["Index"][sample_idx]
        nome_metodo = f"Data: {selected_date} (Idx #{sample_idx})"

        for band in bands:
            band_values[band] = [
                float(ts[band][sample_idx]) for ts in matched_ts
            ]

    df_sentinel_sample = pd.DataFrame(band_values)
    df_emb_features = df_emb_proc[emb_cols].astype(float)

    # 5. Colormap divergente: Vermelho (-1) -> Branco (0) -> Verde (+1)
    cmap_custom = LinearSegmentedColormap.from_list(
        "red_white_green", ["#d73027", "#ffffff", "#1a9850"], N=256
    )

    # 6. Função interna de plotagem
    def calcular_e_plotar(sub_sentinel, sub_emb, subtitulo):
        if len(sub_emb) < 2:
            print(f"Aviso: {subtitulo} tem menos de 2 amostras. Pulando plot.")
            return

        sentinel_valid = sub_sentinel.loc[:, sub_sentinel.std(axis=0) > 0]
        emb_valid = sub_emb.loc[:, sub_emb.std(axis=0) > 0]

        if sentinel_valid.empty or emb_valid.empty:
            print(f"Aviso: Variáveis sem variação em {subtitulo}. Pulando plot.")
            return

        corr_values = np.corrcoef(sentinel_valid.T, emb_valid.T)[
            : len(sentinel_valid.columns), len(sentinel_valid.columns) :
        ]
        corr_matrix = pd.DataFrame(
            corr_values,
            index=sentinel_valid.columns,
            columns=emb_valid.columns,
            dtype=float,
        )
        corr_matrix = corr_matrix.reindex(index=bands, columns=emb_cols)

        plt.figure(figsize=(fig_width, 6))
        sns.heatmap(
            corr_matrix.astype(float),
            cmap=cmap_custom,
            center=0,
            vmin=-1,
            vmax=1,
            cbar_kws={"label": "Correlação de Pearson ($r$)"},
            linewidths=0.1,
            linecolor="#e0e0e0",
        )

        plt.title(
            f"Correlação de Pearson{roi_name}: Embeddings {nome_modelo} ({len(emb_cols)}D) vs. Bandas Sentinel-2\n"
            f"Agregação: {nome_metodo} | {subtitulo} (N = {len(sub_emb)})",
            fontsize=13,
            pad=12,
            fontweight="bold",
        )
        plt.xlabel(f"Dimensões do Embedding {nome_modelo}", fontsize=11, labelpad=8)
        plt.ylabel("Bandas e Índices do Sentinel-2", fontsize=11, labelpad=8)
        plt.xticks(rotation=90, fontsize=7 if len(emb_cols) > 64 else 8)
        plt.yticks(rotation=0, fontsize=10)
        plt.tight_layout()
        plt.show()

    # 7. Disparo por classe ou geral
    if label_col is None:
        calcular_e_plotar(df_sentinel_sample, df_emb_features, "Todas as Amostras")
    else:
        if label_col not in df_emb_proc.columns:
            raise KeyError(f"A coluna '{label_col}' não existe no DataFrame fornecido.")

        classes_unicas = df_emb_proc[label_col].dropna().unique()
        for label in classes_unicas:
            mascara = (df_emb_proc[label_col] == label).values
            calcular_e_plotar(
                df_sentinel_sample.loc[mascara],
                df_emb_features.loc[mascara],
                f"Classe: {label}",
            )

def reduce_embeddings(
    gdf: gpd.GeoDataFrame,
    embedding_type: str = "alphaearth",
    n_components: int = 2,
    method: str = "pca",
    random_state: int = 42,
) -> gpd.GeoDataFrame:
    """Reduz a dimensionalidade dos embeddings (AlphaEarth ou Tessera) em um GeoDataFrame.

    :param gdf: GeoDataFrame contendo as colunas de embedding.
    :param embedding_type: 'alphaearth' (64 dims) ou 'tessera' (128 dims).
    :param n_components: Número de dimensões finais (ex: 2, 3, 16, 32).
    :param method: Algoritmo de redução: 'pca' ou 'tsne'.
    :param random_state: Semente para reprodutibilidade.
    :return: GeoDataFrame com as colunas originais substituídas pelas
        reduzidas.
    """
    gdf_copy = gdf.copy().reset_index(drop=True)
    emb_type = embedding_type.lower()

    # 1. Identificação das colunas de embedding
    if emb_type == "alphaearth":
        col_prefix = "PCA_AE_" if method == "pca" else "TSNE_AE_"
        emb_cols = [
            f"A{i:02d}" for i in range(64) if f"A{i:02d}" in gdf_copy.columns
        ]
    elif emb_type == "tessera":
        col_prefix = "PCA_TES_" if method == "pca" else "TSNE_TES_"
        if "T0" in gdf_copy.columns:
            emb_cols = [
                f"T{i}" for i in range(128) if f"T{i}" in gdf_copy.columns
            ]
        else:
            emb_cols = [
                f"T{i:02d}" for i in range(128) if f"T{i:02d}" in gdf_copy.columns
            ]
    else:
        raise ValueError("embedding_type deve ser 'alphaearth' ou 'tessera'.")

    if not emb_cols:
        raise KeyError(
            f"Nenhuma coluna de embedding encontrada para {embedding_type}."
        )

    # 2. Padronização das variáveis (z-score)
    X = gdf_copy[emb_cols].values
    X_scaled = StandardScaler().fit_transform(X)

    # 3. Aplicação do algoritmo selecionado
    method = method.lower()
    if method == "pca":
        reducer = PCA(n_components=n_components, random_state=random_state)
        X_reduced = reducer.fit_transform(X_scaled)
        var_explicada = reducer.explained_variance_ratio_.sum() * 100
        print(
            f"PCA ({n_components} componentes) - Variância explicada total: {var_explicada:.2f}%"
        )

    elif method == "tsne":
        if n_components > 3:
            raise ValueError(
                "t-SNE é indicado apenas para visualização em 2 ou 3 dimensões (n_components <= 3)."
            )
        reducer = TSNE(n_components=n_components, random_state=random_state)
        X_reduced = reducer.fit_transform(X_scaled)

    else:
        raise ValueError("method deve ser 'pca' ou 'tsne'.")

    # 4. Geração do DataFrame com as novas colunas
    novas_colunas = [f"{col_prefix}{i:02d}" for i in range(n_components)]
    df_features_reduzidas = pd.DataFrame(X_reduced, columns=novas_colunas)

    # 5. Combinação com os metadados e geometrias originais
    cols_para_manter = [c for c in gdf_copy.columns if c not in emb_cols]
    gdf_final = pd.concat(
        [gdf_copy[cols_para_manter], df_features_reduzidas], axis=1
    )

    return gpd.GeoDataFrame(gdf_final, geometry="geometry", crs=gdf.crs)

def plot_reduced_embeddings_2d(
    gdf: gpd.GeoDataFrame,
    label_col: str = "label",
    color_palette: dict | list = None,
    title: str = "Dispersão 2D dos Embeddings Reduzidos",
    figsize=(11, 8),
    alpha: float = 0.7,
    s: int = 40
):
    """
    Plota as duas primeiras dimensões reduzidas geradas por reduce_embeddings.
    
    :param gdf: GeoDataFrame retornado por reduce_embeddings (com 2 dimensões).
    :param label_col: Nome da coluna que contém as classes/rótulos (ex: 'label').
    :param color_palette: Dicionário mapeando classe -> cor (ex: {'floresta': 'green', 'soja': '#f39c12'})
                          ou uma lista de cores (ex: ['#e74c3c', '#2ecc71', '#3498db']).
    :param title: Título do gráfico.
    :param alpha: Transparência dos pontos (0 a 1).
    :param s: Tamanho dos marcadores no gráfico.
    """
    # 1. Identifica automaticamente as colunas geradas pela redução (prefixadas com PCA_ ou TSNE_)
    cols_dims = [c for c in gdf.columns if c.startswith(("PCA_", "TSNE_"))]
    
    if len(cols_dims) < 2:
        raise ValueError(
            f"O DataFrame deve conter pelo menos 2 dimensões reduzidas (encontradas: {cols_dims}). "
            "Execute reduce_embeddings com n_components=2 primeiro."
        )
    
    dim_x, dim_y = cols_dims[0], cols_dims[1]

    if label_col not in gdf.columns:
        raise KeyError(f"A coluna de classes '{label_col}' não foi encontrada no DataFrame.")

    # 2. Configura a figura e estilo
    plt.figure(figsize=figsize)
    sns.set_theme(style="whitegrid")

    # 3. Plota o Scatter Plot com as cores customizadas
    ax = sns.scatterplot(
        data=gdf,
        x=dim_x,
        y=dim_y,
        hue=label_col,
        palette=color_palette,
        alpha=alpha,
        s=s,
        edgecolor="none"
    )

    # 4. Formatação e rótulos
    plt.title(title, fontsize=14, pad=12, fontweight="bold")
    plt.xlabel(dim_x, fontsize=11, labelpad=8)
    plt.ylabel(dim_y, fontsize=11, labelpad=8)

    # Ajusta a legenda para fora do gráfico para não cobrir os dados
    plt.legend(
        title=label_col.capitalize(),
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        borderaxespad=0,
        frameon=True
    )

    plt.tight_layout()
    plt.show()

def plot_reduced_embeddings_3d(
    gdf: gpd.GeoDataFrame,
    label_col: str = "label",
    color_palette: dict | list = None,
    title: str = "Dispersão 3D dos Embeddings Reduzidos",
    figsize=(11, 8),
    elev: int = 25,
    azim: int = 45,
    alpha: float = 0.7,
    s: int = 25,
):
    """Plota as 3 primeiras dimensões reduzidas em um espaço tridimensional (3D).

    :param gdf: GeoDataFrame retornado por reduce_embeddings com n_components=3.
    :param label_col: Nome da coluna de classes/rótulos.
    :param color_palette: Dicionário {'classe': 'cor'} ou lista de cores.
    :param title: Título do gráfico.
    :param elev: Elevação angular da câmera (visão vertical).
    :param azim: Rotação azimutal da câmera (visão horizontal).
    :param alpha: Transparência dos pontos.
    :param s: Tamanho dos marcadores.
    """
    # 1. Identifica automaticamente as colunas geradas pela redução
    cols_dims = [c for c in gdf.columns if c.startswith(("PCA_", "TSNE_"))]

    if len(cols_dims) < 3:
        raise ValueError(
            f"O DataFrame precisa de pelo menos 3 dimensões reduzidas (encontradas: {cols_dims}). "
            "Execute reduce_embeddings com n_components=3 primeiro."
        )

    dim_x, dim_y, dim_z = cols_dims[0], cols_dims[1], cols_dims[2]

    if label_col not in gdf.columns:
        raise KeyError(
            f"A coluna de classes '{label_col}' não foi encontrada no DataFrame."
        )

    # 2. Configura a figura e os eixos 3D
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    classes_unicas = gdf[label_col].dropna().unique()

    # Normaliza a paleta de cores para um dicionário se uma lista for fornecida
    if isinstance(color_palette, list):
        palette_dict = {
            cls: color_palette[i % len(color_palette)]
            for i, cls in enumerate(classes_unicas)
        }
    elif isinstance(color_palette, dict):
        palette_dict = color_palette
    else:
        # Paleta padrão do matplotlib caso o usuário não envie nada
        cmap_padrao = plt.cm.get_cmap("tab10", len(classes_unicas))
        palette_dict = {
            cls: cmap_padrao(i) for i, cls in enumerate(classes_unicas)
        }

    # 3. Plota os pontos classe por classe para garantir as cores e a legenda
    for label in classes_unicas:
        sub = gdf[gdf[label_col] == label]
        cor = palette_dict.get(label, "#333333")

        ax.scatter(
            sub[dim_x],
            sub[dim_y],
            sub[dim_z],
            c=[cor],
            label=str(label),
            alpha=alpha,
            s=s,
            edgecolor="none",
        )

    # 4. Rótulos, visão da câmera e estilização
    ax.set_title(title, fontsize=13, pad=20, fontweight="bold")
    ax.set_xlabel(dim_x, labelpad=10)
    ax.set_ylabel(dim_y, labelpad=10)
    ax.set_zlabel(dim_z, labelpad=10)

    # Ângulo inicial de visão
    ax.view_init(elev=elev, azim=azim)

    # Posiciona a legenda do lado de fora
    ax.legend(
        title=label_col.capitalize(),
        bbox_to_anchor=(1.05, 0.8),
        loc="upper left",
        borderaxespad=0,
    )

    plt.tight_layout()
    plt.show()

def plot_embeddings_density_relief_2d(
    gdf: gpd.GeoDataFrame,
    label_col: str = None,
    color_palette: dict | list = None,
    title: str = "Relevo de Densidade dos Embeddings (2D KDE)",
    figsize = (9, 7),
    cmap: str = "viridis",
    levels: int = 15,
    thresh: float = 0.05,
):
    """Gera um gráfico de relevo/acumulação contínua (Kernel Density Estimation 2D)

    sem exibir pontos de dispersão.

    :param gdf: GeoDataFrame com pelo menos 2 dimensões reduzidas (PCA_* ou
        TSNE_*).
    :param label_col: Nome da coluna de classes. Se None, gera um mapa de
        relevo contínuo único.
    :param color_palette: Dicionário ou lista de cores se label_col for
        informado.
    :param title: Título do gráfico.
    :param cmap: Colormap usado quando label_col for None (ex: 'viridis',
        'magma', 'terrain').
    :param levels: Quantidade de curvas/níveis de elevação do relevo.
    :param thresh: Limiar mínimo de densidade para preenchimento (evita pintar o
        fundo inteiro).
    """
    # 1. Identifica as colunas de dimensões reduzidas
    cols_dims = [c for c in gdf.columns if c.startswith(("PCA_", "TSNE_"))]

    if len(cols_dims) < 2:
        raise ValueError(
            f"O GeoDataFrame deve conter pelo menos 2 dimensões reduzidas. Encontradas: {cols_dims}"
        )

    dim_x, dim_y = cols_dims[0], cols_dims[1]

    plt.figure(figsize=figsize)
    sns.set_theme(style="white")

    # 2. Plotagem do relevo
    if label_col is None:
        # Relevo único contínuo com barra de elevação/densidade
        ax = sns.kdeplot(
            data=gdf,
            x=dim_x,
            y=dim_y,
            fill=True,
            cmap=cmap,
            levels=levels,
            thresh=thresh,
            cbar=True,
            cbar_kws={"label": "Densidade / Acumulação"},
        )
    else:
        if label_col not in gdf.columns:
            raise KeyError(
                f"Coluna '{label_col}' não encontrada no GeoDataFrame."
            )

        # Relevo separado por classe com contornos suaves
        ax = sns.kdeplot(
            data=gdf,
            x=dim_x,
            y=dim_y,
            hue=label_col,
            palette=color_palette,
            fill=True,
            alpha=0.5,
            levels=levels,
            thresh=thresh,
            common_norm=False,
        )

        sns.move_legend(
            ax,
            "upper left",
            bbox_to_anchor=(1.02, 1),
            title=label_col.capitalize(),
            frameon=True,
        )

    # 3. Formatação
    plt.title(title, fontsize=13, pad=12, fontweight="bold")
    plt.xlabel(dim_x, fontsize=11, labelpad=8)
    plt.ylabel(dim_y, fontsize=11, labelpad=8)
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_pca_cumulative_variance(gdf: gpd.GeoDataFrame, title: str = "PCA Análise"):
    """Calcula o PCA completo e plota a curva de variância explicada acumulada

    para AlphaEarth ou Tessera.

    :param gdf: GeoDataFrame com as colunas de embedding (A00..A63 ou
        T0..T127).
    :param title: Título do gráfico (padrão: 'PCA Resultado').
    """
    # 1. Detecta dinamicamente as colunas de embedding (AlphaEarth ou Tessera)
    cols_ae = [
        f"A{i:02d}" for i in range(64) if f"A{i:02d}" in gdf.columns
    ] or [c for c in gdf.columns if c.startswith("A") and c[1:].isdigit()]

    cols_tes = (
        [f"T{i}" for i in range(128) if f"T{i}" in gdf.columns]
        or [f"T{i:02d}" for i in range(128) if f"T{i:02d}" in gdf.columns]
        or [c for c in gdf.columns if c.startswith("T") and c[1:].isdigit()]
    )

    if len(cols_ae) >= 32:
        emb_cols = cols_ae
    elif len(cols_tes) >= 32:
        emb_cols = cols_tes
    else:
        raise KeyError(
            "Não foram encontradas colunas de embedding válidas (AlphaEarth ou Tessera)."
        )

    # 2. Padronização dos dados (z-score)
    X = gdf[emb_cols].dropna().values
    X_scaled = StandardScaler().fit_transform(X)

    # 3. PCA com todos os componentes possíveis
    pca = PCA(n_components=len(emb_cols))
    pca.fit(X_scaled)

    # Variância acumulada
    cum_variance = np.cumsum(pca.explained_variance_ratio_)

    # 4. Plotagem com o mesmo estilo da imagem
    fig, ax = plt.subplots(figsize=(6.5, 5.5))

    ax.plot(range(len(cum_variance)), cum_variance, linewidth=2)

    ax.set_title(title, fontsize=14, pad=15)
    ax.set_xlabel("Number of principal components", fontsize=11, labelpad=6)
    ax.set_ylabel("Cumulative explained variance", fontsize=11, labelpad=6)

    # Grade e limites
    ax.grid(True, linestyle="-", alpha=0.9)
    ax.set_ylim(bottom=min(cum_variance[0] - 0.05, 0.3), top=1.03)

    plt.tight_layout()
    plt.show()
    