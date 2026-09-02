import ee
import time
import json
import geemap.foliumap as geemap
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RectBivariateSpline
from scipy.signal import savgol_filter
from sklearn.decomposition import PCA

import numpy as np
from sklearn.decomposition import PCA
import xarray as xr


def calculate_pca_rgb(image, roi, scale=10, crs_str=None, use_percentiles=True):
    band_names = image.bandNames()
    
    # 1. Compute mean for each band and center the image
    mean_dict = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        crs=crs_str,
        geometry=roi,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=8
    )
    mean_image = image.subtract(mean_dict.toImage(band_names))
    
    # 2. Convert centered bands to a 1D array per pixel: shape [64]
    array_image = mean_image.toArray()
    
    # 3. Compute Covariance Matrix
    covar_dict = array_image.reduceRegion(
        reducer=ee.Reducer.centeredCovariance(),
        crs=crs_str,
        geometry=roi,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=8
    )
    covar_array = ee.Array(covar_dict.get('array'))
    
    # 4. Perform Eigen decomposition
    eigen_dict = covar_array.eigen()
    eigen_vectors = eigen_dict.slice(1, 1)  # shape (64, 64)
    
    # 5. Project centered pixels onto eigenvectors
    array_image_2d = array_image.toArray(1)
    components = ee.Image(eigen_vectors).matrixMultiply(array_image_2d)
    
    # 6. Extract top 3 Principal Components
    pc1 = components.arrayGet([0, 0]).rename('PC1')
    pc2 = components.arrayGet([1, 0]).rename('PC2')
    pc3 = components.arrayGet([2, 0]).rename('PC3')
    pca_raw = ee.Image.cat([pc1, pc2, pc3])
    
    # 7. Min-Max Normalization to [0, 1]
    if use_percentiles:
        # Robust 2%-98% stretch to prevent outlier distortion
        reducer = ee.Reducer.percentile([2, 98])
        min_suffix, max_suffix = '_p2', '_p98'
    else:
        # Absolute min-max
        reducer = ee.Reducer.minMax()
        min_suffix, max_suffix = '_min', '_max'
        
    stats = pca_raw.reduceRegion(
        reducer=reducer,
        crs=crs_str,
        geometry=roi,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=8
    )
    
    min_img = ee.Image.constant([
        stats.get(f'PC1{min_suffix}'),
        stats.get(f'PC2{min_suffix}'),
        stats.get(f'PC3{min_suffix}')
    ])
    
    max_img = ee.Image.constant([
        stats.get(f'PC1{max_suffix}'),
        stats.get(f'PC2{max_suffix}'),
        stats.get(f'PC3{max_suffix}')
    ])
    
    # (X - Min) / (Max - Min), clamped to [0, 1]
    pca_scaled = (
        pca_raw.subtract(min_img)
        .divide(max_img.subtract(min_img))
        .clamp(0.0, 1.0)
        .rename(['R', 'G', 'B'])
    )
    
    return pca_scaled

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
    plt.xticks(range(0, 64, 4))
    plt.ylim(-0.4, 0.4)
    plt.grid(True, alpha=0.3)
    plt.show()

def plot_grid_embedding(embedding, label, values = False):
    embedding = embedding.values
    mean_values = embedding.mean(axis=0)
    Z = mean_values.reshape(8, 8)
    X, Y = np.meshgrid(np.arange(8), np.arange(8))
    
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(
        X, Y, Z,
        cmap='viridis',
        edgecolor='k',
        linewidth=0.5
    )
    if values:
        for i in range(8):
            for j in range(8):
                ax.text(j, i, Z[i, j], f"{Z[i,j]:.3f}", fontsize=7)
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    ax.set_zlabel("Values")
    ax.set_title(f"Grid Embeddings for {label}")
    fig.colorbar(surf, shrink=0.6, label="Embeddings")
    plt.tight_layout()
    plt.show()

def plot_alphaearth_embedding_3d(embedding, label, values=False, smooth_factor=10, cmap='viridis'):
    """
    Plots a 64-dimensional AlphaEarth embedding vector as a smoothed 3D surface.
    
    Parameters:
    - embedding: array-like or DataFrame of shape (64,) or (N, 64)
    - label: str, title/class name for the plot
    - values: bool, whether to display discrete points and numeric labels
    - smooth_factor: int, grid multiplier for interpolation smoothness
    - cmap: str, matplotlib colormap
    """
    # 1. Ensure NumPy array and compute spatial mean if multiple samples are passed
    arr = embedding.values if hasattr(embedding, 'values') else np.asarray(embedding)
    mean_vec = arr.mean(axis=0) if arr.ndim > 1 else arr
    
    if mean_vec.size != 64:
        raise ValueError(f"Expected 64 embedding dimensions, got {mean_vec.size}")
    
    # 2. Reshape into 8x8 spatial grid
    # Z[row, col] -> row=y, col=x
    Z_orig = mean_vec.reshape(8, 8)
    
    x_nodes = np.arange(8)
    y_nodes = np.arange(8)
    
    # 3. Fit 2D cubic spline (kx=3, ky=3)
    spline = RectBivariateSpline(y_nodes, x_nodes, Z_orig, kx=3, ky=3)
    
    # Generate high-resolution continuous meshgrid
    n_pts = 8 * smooth_factor
    x_dense = np.linspace(0, 7, n_pts)
    y_dense = np.linspace(0, 7, n_pts)
    X_dense, Y_dense = np.meshgrid(x_dense, y_dense)
    
    # Evaluate interpolated surface
    Z_smooth = spline(y_dense, x_dense)
    
    # 4. 3D Visualization
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    surf = ax.plot_surface(
        X_dense, Y_dense, Z_smooth,
        cmap=cmap,
        edgecolor='none',
        antialiased=True,
        alpha=0.92,
        rstride=1,
        cstride=1
    )
    
    # Optional contour projection on the bottom XY plane for depth
    z_offset = Z_smooth.min() - 0.05 * (Z_smooth.max() - Z_smooth.min())
    ax.contourf(X_dense, Y_dense, Z_smooth, zdir='z', offset=z_offset, cmap=cmap, alpha=0.3)
    ax.set_zlim(z_offset, Z_smooth.max() + 0.05 * (Z_smooth.max() - Z_smooth.min()))
    
    # 5. Overlay original 64 discrete points and values
    if values:
        X_grid, Y_grid = np.meshgrid(x_nodes, y_nodes)
        ax.scatter(
            X_grid, Y_grid, Z_orig,
            color='crimson',
            s=25,
            edgecolors='white',
            linewidths=0.5,
            label='Discrete Embedding Nodes (64)'
        )
        
        offset_text = 0.02 * (Z_orig.max() - Z_orig.min())
        for r in range(8):      # row (y)
            for c in range(8):  # col (x)
                ax.text(
                    c, r, Z_orig[r, c] + offset_text,
                    f"{Z_orig[r, c]:.2f}",
                    fontsize=6.5,
                    ha='center',
                    va='bottom',
                    color='black'
                )
        ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.8)

    ax.set_xlabel("Grid X (Dim % 8)", labelpad=10)
    ax.set_ylabel("Grid Y (Dim // 8)", labelpad=10)
    ax.set_zlabel("Embedding Intensity", labelpad=10)
    ax.set_title(f"AlphaEarth 64-D Latent Surface — {label}", pad=16, fontweight='bold')
    
    ax.view_init(elev=30, azim=-55)
    fig.colorbar(surf, shrink=0.55, aspect=14, pad=0.1, label="Embedding Amplitude")
    
    plt.tight_layout()
    plt.show()
    