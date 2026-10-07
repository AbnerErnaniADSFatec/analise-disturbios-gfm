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

```
/rasters/aux$ ls -al
total 660617
drwxrwsr-x 3 jovyan users         4 Sep 29 19:30 .
drwxrwsr-x 7 jovyan users         5 Oct  7 14:14 ..
drwxrwsr-x 2 jovyan users         1 Sep 29 19:30 .ipynb_checkpoints
-rw-rw-r-- 1 jovyan users      3360 Sep  1 14:13 amazonia_class.qml
-rw-rw---- 1 jovyan users 676466987 Sep  1 13:47 amazonia_class.tif
-rw-rw-r-- 1 jovyan users       409 Sep  1 14:28 amazonia_class.tif.aux.xml
```

```
mkdir ./datasets/rasters

    alphaearth_mosaic_2024.tif
    cube_sentinel2_2024.nc
```
