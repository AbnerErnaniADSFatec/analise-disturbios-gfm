from osgeo import gdal

gdal.UseExceptions()

dataset_path = "./alphaearth_mosaic_2024.tif"

try:
    ds = gdal.Open(dataset_path)
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    print("GeoTIFF íntegro!")
except Exception as e:
    print(f"Erro de integridade confirmado: {e}")
