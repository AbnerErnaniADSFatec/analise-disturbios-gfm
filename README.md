# analise-disturbios-gfm

Análise de disturbios com base em geospatial foundation models.

Ambiente de testes.

```
conda create --name acrp python=3.11

pip install pyproj==3.7.2

pip install tqdm rioxarray requests aiohttp

pip install fsspec s3fs aiohttp zarr numpy==1.26.4 scipy==1.15.3 pandas==2.2.3 pyarrow==17.0.0 scikit-learn==1.6.1

python3 -m pip install -r requirements.txt

ipython kernel install --user --name acrp
```

#### AlphaEarth

```
pip install earthengine-api geemap

pip install --upgrade anywidget geemap

pip install --upgrade --user geemap xyzservices python-box uninstall -y geemap

pip uninstall -y geemap

pip install rasterio

```

#### Tessera

```
pip install geotessera geopandas shapely

pip install localtileserver
```

#### RS Embed for Python >= 3.12

```
pip install git+https://github.com/cybergis/rs-embed
```

#### Raster path with downloaded data

(https://drive.google.com/drive/folders/14b_a2CKy_UOXCB3XebwXwvMpVxpOL7uw?usp=sharing)[https://drive.google.com/drive/folders/14b_a2CKy_UOXCB3XebwXwvMpVxpOL7uw?usp=sharing]

```
mkdir ./datasets/rasters

    alphaearth_mosaic_2024.tif
    cube_sentinel2_2024.nc
```
