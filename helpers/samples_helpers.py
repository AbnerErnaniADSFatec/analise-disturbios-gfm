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
        subset = da.rio.clip_box(
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

def plot_kde_pca(
    df_pca,
    col="PC1",
    hue_col="label",
    palette=cores_classes,
    show_legend=True,
    legend_title="Classes",
    figsize=(11, 5),
):
    """Plota a densidade (KDE) da componente principal com paleta personalizada

    e controle de legenda.
    """
    plt.figure(figsize=figsize)
    sns.set_theme(style="whitegrid")

    ax = sns.kdeplot(
        data=df_pca,
        x=col,
        hue=hue_col,
        common_norm=False,
        fill=True,
        alpha=0.35,
        linewidth=2,
        palette=palette,
        legend=show_legend,
    )

    # Configuração e posicionamento da legenda fora do gráfico
    if show_legend and ax.get_legend() is not None:
        sns.move_legend(
            ax,
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            title=legend_title,
            frameon=True,
        )

    plt.title(f"Distribuição de Densidade (KDE) - {col}", fontsize=13, pad=12)
    plt.xlabel(col, fontsize=11)
    plt.ylabel("Densidade", fontsize=11)
    plt.tight_layout()
    plt.show()

def plot_distribuicao_dados(
    df: pd.DataFrame,
    class_col: str = "label",
    tipo: str = "perfil",
    feature_prefix: str = "A",
    feature_col: str = None,
    palette: dict | str = cores_classes,
    show_legend: bool = True,
    legend_title: str = None,
    figsize: tuple = (12, 6),
):
    """Gera gráficos de distribuição comparando classes para dados espectrais/temporais.

    Parâmetros:
    ----------
    df : pd.DataFrame
        DataFrame contendo rótulos e variáveis numéricas.
    class_col : str, padrão 'label'
        Nome da coluna categórica para agrupamento ('label' ou 'label_').
    tipo : str, padrão 'perfil'
        'perfil' (média ± 1 DP), 'kde' (densidade) ou 'box' (boxplot).
    feature_prefix : str, padrão 'A'
        Prefixo das colunas numéricas (usado caso feature_col seja None).
    feature_col : str, opcional
        Nome da coluna específica (ex: 'PC1', 'A00'). Se informada, ignora o prefixo.
    palette : dict ou str, padrão cores_classes
        Dicionário mapeando classes a cores hexadecimais ou nome de paleta do Seaborn.
    show_legend : bool, padrão True
        Se True, exibe a legenda formatada fora da área do gráfico.
    legend_title : str, opcional
        Título personalizado da legenda. Se None, assume o valor de class_col.
    figsize : tuple, padrão (12, 6)
        Tamanho da figura (largura, altura).
    """
    title_leg = legend_title if legend_title is not None else class_col

    plt.figure(figsize=figsize)
    sns.set_theme(style="whitegrid")

    # 1. Caso direto: feature_col foi informada explicitamente (ex: 'PC1' ou 'A00')
    if feature_col is not None and feature_col in df.columns:
        if tipo == "kde":
            ax = sns.kdeplot(
                data=df,
                x=feature_col,
                hue=class_col,
                common_norm=False,
                fill=True,
                alpha=0.35,
                linewidth=2,
                palette=palette,
                legend=show_legend,
            )
            plt.title(
                f"Curva de Distribuição de Densidade (KDE) - Variável: {feature_col}",
                fontsize=13,
                pad=12,
            )
            plt.xlabel(f"Valor ({feature_col})", fontsize=11)
            plt.ylabel("Densidade", fontsize=11)

        elif tipo == "box":
            ax = sns.boxplot(
                data=df,
                x=class_col,
                y=feature_col,
                palette=palette,
                showfliers=False,
            )
            plt.title(
                f"Distribuição Boxplot - {feature_col}", fontsize=13, pad=12
            )
            plt.xlabel(class_col, fontsize=11)
            plt.ylabel(feature_col, fontsize=11)

        if show_legend and ax.get_legend() is not None:
            sns.move_legend(
                ax,
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                title=title_leg,
                frameon=True,
            )

        plt.tight_layout()
        plt.show()
        return

    # 2. Caso multivariado: buscar colunas pelo prefixo (ex: A00 a A63)
    feature_cols = [
        c
        for c in df.columns
        if re.match(rf"^{feature_prefix}\d+$", c)
        and pd.api.types.is_numeric_dtype(df[c])
    ]
    feature_cols.sort(key=lambda x: int(re.search(r"\d+", x).group()))

    if not feature_cols:
        raise ValueError(
            f"Nenhuma coluna encontrada com o padrão '{feature_prefix}\\d+'."
        )

    # Opção 1: Perfil de distribuição ao longo de todas as bandas/passos
    if tipo == "perfil":
        df_melted = df.melt(
            id_vars=[class_col],
            value_vars=feature_cols,
            var_name="Band",
            value_name="Valor",
        )

        ax = sns.lineplot(
            data=df_melted,
            x="Band",
            y="Valor",
            hue=class_col,
            estimator="mean",
            errorbar="sd",
            linewidth=2,
            palette=palette,
            legend=show_legend,
        )

        plt.title(
            "Distribuição do Perfil Espectral/Temporal (Média ± 1 Desvio Padrão)",
            fontsize=13,
            pad=12,
        )
        plt.xlabel("Banda / Passo Temporal", fontsize=11)
        plt.ylabel("Valor", fontsize=11)

        ticks = range(0, len(feature_cols), max(1, len(feature_cols) // 16))
        ax.set_xticks(ticks)
        ax.set_xticklabels(
            [feature_cols[i] for i in ticks], rotation=45, ha="right"
        )

    # Opção 2: Estimativa de Densidade de Kernel (KDE) da primeira banda
    elif tipo == "kde":
        col_alvo = feature_cols[0]
        ax = sns.kdeplot(
            data=df,
            x=col_alvo,
            hue=class_col,
            common_norm=False,
            fill=True,
            alpha=0.35,
            linewidth=2,
            palette=palette,
            legend=show_legend,
        )
        plt.title(
            f"Curva de Distribuição de Densidade (KDE) - Variável: {col_alvo}",
            fontsize=13,
            pad=12,
        )
        plt.xlabel(f"Valor ({col_alvo})", fontsize=11)
        plt.ylabel("Densidade", fontsize=11)

    # Opção 3: Boxplot comparativo de bandas amostradas
    elif tipo == "box":
        sub_cols = feature_cols[:: max(1, len(feature_cols) // 8)]
        df_melted = df.melt(
            id_vars=[class_col],
            value_vars=sub_cols,
            var_name="Band",
            value_name="Valor",
        )

        ax = sns.boxplot(
            data=df_melted,
            x="Band",
            y="Valor",
            hue=class_col,
            palette=palette,
            showfliers=False,
        )
        plt.title(
            "Distribuição dos Valores por Classe (Boxplot sem Outliers)",
            fontsize=13,
            pad=12,
        )
        plt.xlabel("Variáveis Selecionadas", fontsize=11)
        plt.ylabel("Valor", fontsize=11)

    # Ajusta legenda externa para os modos multivariados
    if show_legend and ax.get_legend() is not None:
        sns.move_legend(
            ax,
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            title=title_leg,
            frameon=True,
        )
    elif not show_legend and ax.get_legend() is not None:
        ax.get_legend().remove()

    plt.tight_layout()
    plt.show()


def calcular_pca_nd(
    df: pd.DataFrame, n_components: int | float = 2, feature_prefix: str = "A"
) -> tuple[pd.DataFrame, PCA]:
    """Calcula N Componentes Principais para as colunas numéricas e anexa ao DataFrame.

    Parâmetros:
    ----------
    df : pd.DataFrame
        DataFrame contendo as variáveis espectrais/temporais.
    n_components : int ou float, padrão 2
        - Se int (ex: 2, 3, 5): número exato de dimensões a extrair.
        - Se float (ex: 0.95): extrai dimensões suficientes para reter X% da variância.
    feature_prefix : str, padrão 'A'
        Prefixo das colunas numéricas de interesse.

    Retorna:
    -------
    df_result : pd.DataFrame
        DataFrame com as novas colunas adicionadas ('PC1', 'PC2', ...).
    pca : PCA
        Objeto ajustado do sklearn com os atributos de variância e pesos.
    """
    # 1. Seleciona e ordena as colunas pelo prefixo (ex: A00 a A63)
    cols = [
        c
        for c in df.columns
        if re.match(rf"^{feature_prefix}\d+$", c)
        and pd.api.types.is_numeric_dtype(df[c])
    ]
    cols.sort(key=lambda x: int(re.search(r"\d+", x).group()))

    # 2. Padroniza os dados
    x_scaled = StandardScaler().fit_transform(df[cols])

    # 3. Ajusta o PCA para N componentes
    pca = PCA(n_components=n_components, random_state=42)
    pcs = pca.fit_transform(x_scaled)

    # 4. Cria nomes para as colunas (PC1, PC2, ..., PCn)
    pc_cols = [f"PC{i+1}" for i in range(pcs.shape[1])]
    df_pcs = pd.DataFrame(pcs, columns=pc_cols, index=df.index)

    # 5. Exibe o resumo da variância explicada
    for i, ratio in enumerate(pca.explained_variance_ratio_):
        print(f"{pc_cols[i]}: {ratio * 100:.2f}% da variância")
    print(f"Total acumulado: {pca.explained_variance_ratio_.sum() * 100:.2f}%\n")

    # 6. Concatena de volta ao DataFrame original
    df_result = pd.concat([df, df_pcs], axis=1)

    return df_result, pca
