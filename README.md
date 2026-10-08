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
/rasters$ ls -Ral
.:
total 0
drwxrwsr-x 7 jovyan users  5 Oct  7 14:14 .
drwxrwsr-x 3 jovyan users  1 Oct  1 19:58 ..
drwxrwsr-x 2 jovyan users  0 Sep 29 19:30 .ipynb_checkpoints
drwxrwsr-x 3 jovyan users 23 Oct  7 21:18 alphaearth
drwxrwsr-x 3 jovyan users  5 Oct  8 14:22 aux
drwxrwsr-x 3 jovyan users 12 Oct  2 19:51 cubes
drwxrwsr-x 3 jovyan users 10 Oct  8 12:58 tessera

./.ipynb_checkpoints:
total 0
drwxrwsr-x 2 jovyan users 0 Sep 29 19:30 .
drwxrwsr-x 7 jovyan users 5 Oct  7 14:14 ..

./alphaearth:
total 11453860
drwxrwsr-x 3 jovyan users         23 Oct  7 21:18 .
drwxrwsr-x 7 jovyan users          5 Oct  7 14:14 ..
drwxrwsr-x 2 jovyan users          0 Oct  7 13:25 .ipynb_checkpoints
-rw-rw---- 1 jovyan users 1073492335 Oct  6 21:19 alphaearth_2022_C44L39.tif
-rw-rw-r-- 1 jovyan users  100119016 Oct  7 14:15 alphaearth_2022_C44L39_pca.tif
-rw-rw-r-- 1 jovyan users    1500537 Oct  7 21:18 alphaearth_2022_C44L39_pca.tif.aux.xml
-rw-rw---- 1 jovyan users 1076544274 Oct  6 21:20 alphaearth_2022_C51L34.tif
-rw-rw-r-- 1 jovyan users  100464524 Oct  7 14:16 alphaearth_2022_C51L34_pca.tif
-rw-rw---- 1 jovyan users 1072494934 Oct  6 21:19 alphaearth_2022_C51L41.tif
-rw-rw-r-- 1 jovyan users   99232181 Oct  7 14:13 alphaearth_2022_C51L41_pca.tif
-rw-rw---- 1 jovyan users 1071537733 Oct  6 21:11 alphaearth_2022_C56L49.tif
-rw-rw-r-- 1 jovyan users  100105063 Oct  7 14:14 alphaearth_2022_C56L49_pca.tif
-rw-rw---- 1 jovyan users 1066831704 Oct  6 21:11 alphaearth_2022_C60L63.tif
-rw-rw-r-- 1 jovyan users  102436160 Oct  7 14:13 alphaearth_2022_C60L63_pca.tif
-rw-rw---- 1 jovyan users 1072870621 Oct  6 19:44 alphaearth_2024_C44L39.tif
-rw-rw-r-- 1 jovyan users  100084922 Oct  7 14:06 alphaearth_2024_C44L39_pca.tif
-rw-rw---- 1 jovyan users 1075725222 Oct  6 21:33 alphaearth_2024_C51L34.tif
-rw-rw-r-- 1 jovyan users  100495499 Oct  7 14:11 alphaearth_2024_C51L34_pca.tif
-rw-rw---- 1 jovyan users 1072617842 Oct  6 21:30 alphaearth_2024_C51L41.tif
-rw-rw-r-- 1 jovyan users   99387396 Oct  7 14:10 alphaearth_2024_C51L41_pca.tif
-rw-rw---- 1 jovyan users 1072459881 Oct  6 21:35 alphaearth_2024_C56L49.tif
-rw-rw-r-- 1 jovyan users   99834231 Oct  7 14:11 alphaearth_2024_C56L49_pca.tif
-rw-rw---- 1 jovyan users 1068582939 Oct  6 21:21 alphaearth_2024_C60L63.tif
-rw-rw-r-- 1 jovyan users  101924420 Oct  7 14:09 alphaearth_2024_C60L63_pca.tif
-rw-rw-r-- 1 jovyan users       6063 Oct  7 14:02 logs.txt

./alphaearth/.ipynb_checkpoints:
total 0
drwxrwsr-x 2 jovyan users  0 Oct  7 13:25 .
drwxrwsr-x 3 jovyan users 23 Oct  7 21:18 ..

./aux:
total 1313787
drwxrwsr-x 3 jovyan users         5 Oct  8 14:22 .
drwxrwsr-x 7 jovyan users         5 Oct  7 14:14 ..
drwxrwsr-x 2 jovyan users         0 Oct  8 14:18 .ipynb_checkpoints
-rw-r--r-- 1 jovyan users      8753 Oct  8 14:22 amazonia_class_2022.qml
-rw-r--r-- 1 jovyan users 668837230 Oct  8 14:28 amazonia_class_2022.tif
-rw-r--r-- 1 jovyan users      3360 Oct  8 14:22 amazonia_class_2024.qml
-rw-r--r-- 1 jovyan users 676466987 Oct  8 14:28 amazonia_class_2024.tif

./aux/.ipynb_checkpoints:
total 0
drwxrwsr-x 2 jovyan users 0 Oct  8 14:18 .
drwxrwsr-x 3 jovyan users 5 Oct  8 14:22 ..

./cubes:
total 52844485
drwxrwsr-x 3 jovyan users         12 Oct  2 19:51 .
drwxrwsr-x 7 jovyan users          5 Oct  7 14:14 ..
drwxrwsr-x 2 jovyan users          1 Sep 30 14:45 .ipynb_checkpoints
-rw-rw-r-- 1 jovyan users 5583738743 Oct  2 18:35 cube_sentinel2_2022_C44L39.nc
-rw-rw-r-- 1 jovyan users 5501086757 Oct  2 19:51 cube_sentinel2_2022_C51L34.nc
-rw-rw-r-- 1 jovyan users 5527149541 Oct  2 14:12 cube_sentinel2_2022_C51L41.nc
-rw-rw-r-- 1 jovyan users 5502380507 Oct  2 15:57 cube_sentinel2_2022_C56L49.nc
-rw-rw-r-- 1 jovyan users 4392908028 Sep 30 20:52 cube_sentinel2_2022_C60L63.nc
-rw-rw-r-- 1 jovyan users 5583738743 Sep 30 18:39 cube_sentinel2_2024_C44L39.nc
-rw-rw-r-- 1 jovyan users 5501086757 Aug 31 22:19 cube_sentinel2_2024_C51L34.nc
-rw-rw-r-- 1 jovyan users 5527149541 Aug 20 23:25 cube_sentinel2_2024_C51L41.nc
-rw-rw-r-- 1 jovyan users 5502380507 Sep 30 16:25 cube_sentinel2_2024_C56L49.nc
-rw-rw-r-- 1 jovyan users 5491120349 Aug 31 23:22 cube_sentinel2_2024_C60L63.nc
-rw-rw-r-- 1 jovyan users      10754 Oct  6 19:27 logs.txt

./cubes/.ipynb_checkpoints:
total 1
drwxrwsr-x 2 jovyan users   1 Sep 30 14:45 .
drwxrwsr-x 3 jovyan users  12 Oct  2 19:51 ..
-rw-rw-r-- 1 jovyan users 840 Sep 30 14:45 logs-checkpoint.txt

./tessera:
total 6975316
drwxrwsr-x 3 jovyan users         10 Oct  8 12:58 .
drwxrwsr-x 7 jovyan users          5 Oct  7 14:14 ..
drwxr-sr-x 2 jovyan users          1 Oct  8 12:58 .ipynb_checkpoints
-rw-rw-r-- 1 jovyan users        194 Oct  8 14:24 logs.txt
-rw-rw-r-- 1 jovyan users 3471972801 Aug 31 15:02 tessera_2024_C51L34.tif
-rw-rw-r-- 1 jovyan users    1579329 Aug 31 16:05 tessera_2024_C51L34.tif.aux.xml
-rw-rw-r-- 1 jovyan users   99585751 Sep  1 16:46 tessera_2024_C51L34_pca.tif
-rw-rw-r-- 1 jovyan users    1502109 Sep  1 19:05 tessera_2024_C51L34_pca.tif.aux.xml
-rw-rw-r-- 1 jovyan users 3465498501 Aug 26 16:17 tessera_2024_C51L41.tif
-rw-rw-r-- 1 jovyan users    1581517 Aug 31 16:05 tessera_2024_C51L41.tif.aux.xml
-rw-rw-r-- 1 jovyan users   99501695 Sep  1 16:45 tessera_2024_C51L41_pca.tif
-rw-rw-r-- 1 jovyan users    1499164 Sep  1 19:05 tessera_2024_C51L41_pca.tif.aux.xml

./tessera/.ipynb_checkpoints:
total 1
drwxr-sr-x 2 jovyan users  1 Oct  8 12:58 .
drwxrwsr-x 3 jovyan users 10 Oct  8 12:58 ..
-rw-rw-r-- 1 jovyan users 97 Oct  7 14:58 logs-checkpoint.txt
```
