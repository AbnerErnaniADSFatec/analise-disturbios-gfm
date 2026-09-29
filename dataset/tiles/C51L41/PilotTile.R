# pilot Reference Dataset C51L41

library(tidyverse)
library(terra)
library(tidyterra)
library(sf)
library(mapview)

sf::sf_use_s2(FALSE)

# tile Deter #####
# for the tile C51L41 ####
tiles_Deter <- read_sf("D:/NextCloudMirror/data/tiles/Deter/deter_tiles_ALB.shp")
tiles_Deter_WGS84 <- st_transform(tiles_Deter, 4326)
tiles_Deter_WGS84 |> filter(id == "C51L41") -> tile_C51L41
tiles_Deter |> filter(id == "C51L41") -> tile_C51L41_s

write_sf(tile_C51L41, "tile_C51L41_WGS84.gpkg")

# alerts ####
# GWF ####
GWF_2019_2025 <- rast("D:/NextCloudMirror/data/alerts/GFW/tifs/GFW_ALB.tiff")
GFW_C51L41 <- crop(GWF_2019_2025, tile_C51L41)
as_date(2410, origin = "2015-01-01")-1
as_date(4014, origin = "2015-01-01")-1

plot(GFW_C51L41)
GFW_C51L41_l <- clamp(GFW_C51L41, lower = 20000, upper = 29999, values = FALSE)-20000
GFW_C51L41_hh <- clamp(GFW_C51L41, lower = 30000, upper = 39999, values = FALSE)-30000
GFW_C51L41_ht <- clamp(GFW_C51L41, lower = 40000, upper = 49999, values = FALSE)-40000

GFW_C51L41 <- min(GFW_C51L41_ht,GFW_C51L41_hh,GFW_C51L41_l,na.rm = TRUE)
as_date(1484, origin = "2015-01-01")-1
as_date(4014, origin = "2015-01-01")-1

as.Date("2020-01-01") - as.Date("2015-01-01") + 1 # 1827
GFW_C51L41 <- GFW_C51L41 - 1827
as_date(2191, origin = "2020-01-01")

as.numeric(as.Date("2024-12-31") - as.Date("2020-01-01")) + 1 # 1827
GFW_C51L41_20_24 <- ifel(GFW_C51L41 >= 1, GFW_C51L41, NA)
as_date(1827, origin = "2020-01-01") - 1
GFW_C51L41 <- ifel(GFW_C51L41_20_24 <= 1826, GFW_C51L41_20_24, NA)
plot(GFW_C51L41)

# RADD ####
RADD_2020_2024 <- rast("D:/NextCloudMirror/data/alerts/RADD/tifs/RADD_ALB_DOY.tif")
RADD_C51L41 <- crop(RADD_2020_2024, tile_C51L41)
RADD_C51L41 <- resample(RADD_C51L41, GFW_C51L41)
plot(RADD_C51L41)

RADD_C51L41_l <- clamp(RADD_C51L41, lower = 20000, upper = 29999, values = FALSE)-20000
RADD_C51L41_h <- clamp(RADD_C51L41, lower = 30000, upper = 39999, values = FALSE)-30000
RADD_C51L41 <- min(RADD_C51L41_h, RADD_C51L41_l, na.rm = TRUE)
as_date(1828, origin = "2015-01-01") -1
as_date(4018, origin = "2015-01-01") -1 # 5*365
RADD_C51L41 <- RADD_C51L41 - 1827
RADD_C51L41 <- ifel(RADD_C51L41 <= 1826, RADD_C51L41, NA)
plot(RADD_C51L41)

# GLADS2 ####
GLADS2_2020_2024 <- rast("D:/NextCloudMirror/data/alerts/GLAD_S2/tifs/GLADS2_2020_2024.tif")
GLADS2_C51L41 <- crop(GLADS2_2020_2024, tile_C51L41)
GLADS2_C51L41 <- resample(GLADS2_C51L41, GFW_C51L41)
plot(GLADS2_C51L41)
GLADS2_C51L41 <- GLADS2_C51L41-364
plot(GLADS2_C51L41)

# GLADL ####
GLADL_2020_2024 <- rast("D:/NextCloudMirror/data/alerts/GLAD_L/tifs/GLADL_20_24.tif")
GLADL_C51L41 <- crop(GLADL_2020_2024, tile_C51L41)
GLADL_C51L41 <- resample(GLADL_C51L41, GFW_C51L41)
plot(GLADL_C51L41)

# GFW - GLADL by exclusion
s_GFW <- c(RADD_C51L41, GLADS2_C51L41, GFW_C51L41)
names(s_GFW) <- c("RADD","GLADS2","GLADL_GFW")
GFW_C51L41m <- min(s_GFW, na.rm = TRUE)
min_layer_GFW <- app(s_GFW, which.min, na.rm = TRUE)
layer_names_GFW <- names(s_GFW)
min_source_GFW <- subst(min_layer_GFW, 1:length(layer_names_GFW), layer_names_GFW)
names(GFW_C51L41m) <- "GWF"

plot(GFW_C51L41m, main="Minimum Values")
plot(min_source_GFW, main="Source Layer")

# Tropisco ####
Tropisco_2020_2024 <- rast("D:/NextCloudMirror/data/alerts/Tropisco/tifs/tropisco20_24_doy.tif")
Tropisco_C51L41 <- crop(Tropisco_2020_2024, tile_C51L41)
Tropisco_C51L41 <- resample(Tropisco_C51L41, GFW_C51L41)
names(Tropisco_C51L41) <- "tropisco"
plot(Tropisco_C51L41)

# LUCA ####
LUCA_2020_2024 <- rast("D:/NextCloudMirror/data/alerts/LUCA/tifs/LUCA_doy.tiff")
LUCA_C51L41 <- crop(LUCA_2020_2024, tile_C51L41)
LUCA_C51L41 <- resample(LUCA_C51L41, GFW_C51L41)
plot(LUCA_C51L41)
as_date(18263, origin = "1970-01-01") -1
as.Date("2020-01-01") - as.Date("1970-01-01") + 1 #18263 
LUCA_C51L41 <- LUCA_C51L41 - 18262
plot(LUCA_C51L41)

# min Date ####
#Combine them into a multi-layer SpatRaster
s_aut <- c(GFW_C51L41m, Tropisco_C51L41, LUCA_C51L41)
names(s_aut) <- c("GFW","Tropisco","LUCA")
#Calculate the minimum value per pixel
Aut_C51L41 <- min(s_aut, na.rm = TRUE)
#Find which layer index (1 or 2) holds the minimum value per pixel
min_layer <- app(s_aut, which.min, na.rm = TRUE)

# Optional: Map the index numbers back to the actual raster names
layer_names <- names(s_aut)
min_source <- subst(min_layer, 1:length(layer_names), layer_names)

# Plot results
plot(Aut_C51L41, main="Minimum Values")
plot(min_source, main="Source Layer")

# Final raster ####
names(Aut_C51L41) <- "doy_minAut"
writeRaster(Aut_C51L41, "Aut_C51L41.tif")

Raster_C51L41 <- c(Aut_C51L41, Tropisco_C51L41, LUCA_C51L41, GFW_C51L41,
                   RADD_C51L41, GLADS2_C51L41, GLADL_C51L41)
names(Raster_C51L41) <- c("minAut_doy20", "Tropisco_doy20","LUCA_doy20","GFW_doy20",
                          "RADD_doy20","GLAS2_doy20","GLADL_doy20")
writeRaster(Raster_C51L41, "Raster_C51L41.tif", overwrite=TRUE)

Aut_C51L41 <- as.int(round(Aut_C51L41, 0))

# rater per doy ####
Aut_C51L41f <- as.factor(Aut_C51L41)
# u_vals <- sort(unique(values(Aut_C51L41f)))
# Aut_C51L41_perdoy <- segregate(Aut_C51L41, keep = FALSE)
# plot(Aut_C51L41_perdoy[[10]], colNA = "black", col = c("magenta", "yellow"))
# 
# time(Aut_C51L41_perdoy) <- as_date(u_vals, origin = "2020-01-01")-1
# names(Aut_C51L41_perdoy) <- paste0("doy_", u_vals)
# 
# Aut_C51L41_1 <- subst(Aut_C51L41_perdoy, 0, NA)
# Aut_C51L41_1 <- subst(Aut_C51L41_1, NA, 0)
# plot(Aut_C51L41_1[[75]], colNA = "black", col = c("magenta", "yellow"))
# 
# Aut_C51L41_1ac <- cummax(Aut_C51L41_1)
# plot(Aut_C51L41_1ac[[1000]], colNA = "black", col = c("magenta", "yellow"))
# writeRaster(Aut_C51L41_1ac, "Aut_C51L41_1ac.tif")
# Aut_C51L41_1ac <- rast("Aut_C51L41_1ac.tif")
#
# Generate a vector of specific filenames using the layer names
# file_names <- paste0("~/grupos/projeto-dedicado/Alby/Py4Track/input_C51L41/",
#                      "C51L41_", gsub("-", "", time(Aut_C51L41_1ac)), ".tif")
#
# Write each layer to its respective file
# writeRaster(Aut_C51L41_1ac, filename = file_names, overwrite = TRUE)

# alerts polygons ####
# plot(Aut_C51L41_1ac[[1817]])
# Aut_C51L41_20_24NA <- subst(Aut_C51L41_1ac[[1817]], 0, NA)
# plot(Aut_C51L41_20_24NA, colNA = "black", col = c("magenta"))


# polygons alerts ####
Aut_C51L41_sf <- st_as_sf(as.polygons(Aut_C51L41f))

Aut_C51L41_sf |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geometry)) -> Aut_C51L41_sf

mapview(Aut_C51L41_sf)
names(Aut_C51L41_sf)[1] <- "doy_2020"
Aut_C51L41_sf$date <- as_date(as.integer(Aut_C51L41_sf$doy_2020), origin = "2020-01-01")-1

Aut_C51L41_sf |> mutate(doy_2020 = as.integer(doy_2020)) -> Aut_C51L41_sf
mapview(Aut_C51L41_sf, zcol="doy_2020", alpha = 0)

write_sf(Aut_C51L41_sf, "Aut_C51L41_sf.gpkg")

# Class identification ####

# Layers ####

# GLADS2 mask NA / 1 ####
MaskGLAD <- rast("D:/NextCloudMirror/data/masks/MaskGLADS2_ALBNA.tif")
MaskGLADS2_C51L41 <- crop(MaskGLAD, tile_C51L41)
plot(MaskGLADS2_C51L41)

MaskGLADS2_C51L41_sf <- st_as_sf(as.polygons(MaskGLADS2_C51L41))

MaskGLADS2_C51L41_sf |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geometry)) -> MaskGLADS2_C51L41_sf

names(MaskGLADS2_C51L41_sf)[1] <- "maskGLADS2"

rm(MaskGLAD)

# Wetland ####
Wetland <- rast("D:/NextCloudMirror/data/auxiliars/ALB_LBA_Amazon_wetland_dual-season_veg_flood_3arcsec.tif")
Wetland_C51L41 <- crop(Wetland, tile_C51L41)

Wetland_C51L41_sf <- st_as_sf(as.polygons(Wetland_C51L41))

Wetland_C51L41_sf |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geometry)) -> Wetland_C51L41_sf

names(Wetland_C51L41_sf)[1] <- "wetland"

rm(Wetland)

# GSW ####
GSW_recurence <- rast("D:/NextCloudMirror/data/auxiliars/Global_Surface_Water/recurence_ALB.tif")
GSW_C51L41 <- crop(GSW_recurence, tile_C51L41)

GSW_C51L41_sf <- st_as_sf(as.polygons(GSW_C51L41))

GSW_C51L41_sf |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geometry)) -> GSW_C51L41_sf

names(GSW_C51L41_sf)[1] <- "GSW_rec"

GSW_C51L41_sf |> filter(GSW_rec!=0) -> GSW_C51L41_water

rm(GSW_recurence)

# TerraClass 2020 ####
terraClass <- rast("D:/NextCloudMirror/data/auxiliars/AMZ.2020.M.tif")
terraClass_C51L41 <- crop(terraClass, tile_C51L41_s)

terraClass_C51L41_sf <- st_as_sf(as.polygons(terraClass_C51L41))

terraClass_C51L41_sf |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geometry)) -> terraClass_C51L41_sf

names(terraClass_C51L41_sf)[1] <- "TC2020"

rm(terraClass)

terraClass_C51L41_sf |> filter(TC2020 != 1) -> terraClass_C51L41_sf
unique(terraClass_C51L41_sf$TC2020)
terraClass_C51L41_sf$TC2020[terraClass_C51L41_sf$TC2020 == 2] <- "SecVeg"    # "#0fc80f"
terraClass_C51L41_sf$TC2020[terraClass_C51L41_sf$TC2020 == 10] <- "Pasture"  # "#e6a04b"
terraClass_C51L41_sf$TC2020[terraClass_C51L41_sf$TC2020 == 11] <- "Pasture"  # "#ffec87"
terraClass_C51L41_sf$TC2020[terraClass_C51L41_sf$TC2020 == 20] <- "Others"   # "#e1e1e1"#
terraClass_C51L41_sf$TC2020[terraClass_C51L41_sf$TC2020 == 22] <- "Deforestation"    # "#ff0000"
terraClass_C51L41_sf$TC2020[terraClass_C51L41_sf$TC2020 == 23] <- "Water"   # "#0000ff"#
terraClass_C51L41_sf$TC2020[terraClass_C51L41_sf$TC2020 == 51] <- "NoForest" # "#b4d79e"

#            Nome da Classe                          colour             Valor Digital da  Imagem
"#005500"# VEGETACAO NATURAL FLORESTAL PRIMARIA    #005500 0 85 0             1
"#0fc80f"# VEGETACAO NATURAL FLORESTAL SECUNDARIA  #0fc80f 15 200 15          2
"#a8a800"# SILVICULTURA                            #a8a800 168 168 0          9
"#e6a04b"# PASTAGEM ARBUSTIVA/ARBOREA              #e6a04b 230 160 75         10
"#ffec87"# PASTAGEM HERBACEA                       #ffec87 255 236 135        11
"#ff8828"# CULTURA AGRICOLA PERENE                 #ff8828 255 136 40         12
"#996400"# CULTURA AGRICOLA SEMIPERENE             #996400 153 100 0          13
"#FFE300"# CULTURA AGRICOLA TEMPORARIA DE 1 CICLO  #FFE300 255 227 0          14
"#FFFF00"# CULTURA AGRICOLA TEMPORARIA + 1 CICLO   #FFFF00 255 255 0          15
"#ad89cd"# MINERACAO                               #ad89cd 173 137 205        16
"#ffa8c0"# URBANIZADA                              #ffa8c0 255 168 192        17
"#e1e1e1"# Outros Usos                             #e1e1e1                    20
"#ff00c5"# Outras Áreas Edificadas                 #ff00c5                    21
"#ff0000"# DESFLORESTAMENTO NO ANO                 #ff0000 255 0 0            22
"#0000ff"# CORPO DAGUA                             #0000ff 0 0 255            23
"#ffffff"# Não Observado                           #ffffff                    25
"#b4d79e"# Natural NAO FLORESTA                    #ff00ff 225 225 225        51

terraClass_C51L41_sf <- st_transform(terraClass_C51L41_sf, 4326)

unique(terraClass_C51L41_sf$TC2020)
terraClass_C51L41_sf |> filter(TC2020 == "NoForest") -> terraClass_C51L41_sf_NF

terraClass_C51L41_sf |> filter(TC2020 == "Water") -> terraClass_C51L41_sf_Water

terraClass_C51L41_sf |> filter(TC2020 == "SecVeg") -> terraClass_C51L41_sf_SecVeg

terraClass_C51L41_sf |> filter(TC2020 == "Deforestation") -> terraClass_C51L41_sf_Def

terraClass_C51L41_sf |> filter(TC2020 == "Pasture" | TC2020 == "Others") -> terraClass_C51L41_sf_oth


# WorldCover 2021 ####
WORLDCOVER <- rast("D:/NextCloudMirror/data/auxiliars/WORLDCOVER2021.tif")
WORLDCOVER_C51L41 <- crop(WORLDCOVER, tile_C51L41)

WORLDCOVER_C51L41_sf <- st_as_sf(as.polygons(WORLDCOVER_C51L41))

WORLDCOVER_C51L41_sf |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geometry)) -> WORLDCOVER_C51L41_sf

unique(WORLDCOVER_C51L41_sf$ESA_WorldCover_10m_2021_v200_N00W051_Map)
names(WORLDCOVER_C51L41_sf)[1] <- "WC2021"

# Color   Value    	Class Name
"#006400" # 10 	 	# Tree cover
"#ffbb22" # 20 		#	Shrubland
"#ffff4c" # 30 		#	Grassland
"#f096ff" # 40 	  #	Cropland
"#fa0000" # 50 		#	Built up
"#b4b4b4" # 60 		#	Bare /sparse vegetation
"#f0f0f0" # 70 		#	Snow and Ice
"#0064c8" # 80 		#	Permanent water bodies
"#0096a0" # 90 		#	Herbaceous wetland
"#00cf75" # 95 		 	Mangroves
"#fae6a0" #100 	  	Moss and lichen
"#"       #  0     	No data

WORLDCOVER_C51L41_sf |> filter(WC2021 != 10) -> WORLDCOVER_C51L41_sf
unique(WORLDCOVER_C51L41_sf$WC2021)
#mapview(WORLDCOVER_C51L41_sf, zcol = "WC2021")
WORLDCOVER_C51L41_sf$WC2021[WORLDCOVER_C51L41_sf$WC2021 == 20] <- "Shrubland"  # "#e6a04b"
WORLDCOVER_C51L41_sf$WC2021[WORLDCOVER_C51L41_sf$WC2021 == 30] <- "Grassland"  # "#ffec87"
WORLDCOVER_C51L41_sf$WC2021[WORLDCOVER_C51L41_sf$WC2021 == 50] <- "Builtup"   # "#e1e1e1"#
WORLDCOVER_C51L41_sf$WC2021[WORLDCOVER_C51L41_sf$WC2021 == 60] <- "BareSoil"    # "#ff0000"
WORLDCOVER_C51L41_sf$WC2021[WORLDCOVER_C51L41_sf$WC2021 == 80] <- "Water"   # "#0000ff"#
WORLDCOVER_C51L41_sf$WC2021[WORLDCOVER_C51L41_sf$WC2021 == 90] <- "Wetland" # "#b4d79e"

rm(WORLDCOVER)

unique(WORLDCOVER21_C51L41$WC2021)
WORLDCOVER21_C51L41 |> filter(WC2021 == "Water") -> WORLDCOVER21_C51L41_Water

WORLDCOVER21_C51L41 |> filter(WC2021 == "Wetland") -> WORLDCOVER21_C51L41_Wetland

# SecVeg ####
Secondary_Vegetation <- read_sf("D:/NextCloudMirror/data/auxiliars/old_amostras/SecVeg_DeterInters.shp")
Secondary_Vegetation |> filter(id == "C51L41") -> Sec_Veg_C51L41

# IBGE hydr ####
polys_IBGE <- read_sf("D:/NextCloudMirror/data/auxiliars/hydro/polys_IBGE_QGIS.gpkg")
polys_IBGE_C51L41 <- st_intersection(polys_IBGE, tile_C51L41_s)
polys_IBGE_C51L41 <- st_transform(polys_IBGE_C51L41, 4326)

# IBGE rod hydr ####
hydr_rod <- read_sf("D:/NextCloudMirror/data/auxiliars/hydro/lines_IBGE_hid_rod_ALB.gpkg")
hydr_rod$layer <- recode(hydr_rod$layer,
                         "bc250_2026-03-03 — hid_trecho_drenagem_l" = "RiverDrain",
                         "bc250_2026-03-03 — rod_trecho_rodoviario_l" = "Road")
hydr_rod_C51L41 <- st_intersection(hydr_rod, tile_C51L41_s)

# Alerts BR ####

Deter_noOverlap <- read_sf("D:/NextCloudMirror/data/alerts/Deter/Deter_noOverlap_tiledQGIS.gpkg")
Deter_noOverlap |> filter(id == "C51L41") -> Deter20_24_C51L41

unique(Deter20_24_C51L41$CLASS)
Deter20_24_C51L41$CLASS[Deter20_24_C51L41$CLASS %in% c("DESMATAMENTO_CR", "DESMATAMENTO_VEG")] <- "Deforestation_CR"
Deter20_24_C51L41$CLASS[Deter20_24_C51L41$CLASS %in% c("DEGRADACAO", "CS_GEOMETRICO", "CS_DESORDENADO")] <- "Degradation_CS"
Deter20_24_C51L41$CLASS[Deter20_24_C51L41$CLASS == "CICATRIZ_DE_QUEIMADA"] <- "FireScars_CzQ"

Deter20_24_C51L41 <- st_transform(Deter20_24_C51L41, 4326)

# Prodes ####
st_layers("D:/NextCloudMirror/data/auxiliars/OSM/prodes_amazonia_legal_v20260717.gpkg/prodes_amazonia_legal_v20260717.gpkg")

accumulated_deforestation_2007 <- read_sf("D:/NextCloudMirror/data/auxiliars/OSM/prodes_amazonia_legal_v20260717.gpkg/prodes_amazonia_legal_v20260717.gpkg",layer = "accumulated_deforestation_2007")
yearly_deforestation <- st_read("D:/NextCloudMirror/data/auxiliars/OSM/prodes_amazonia_legal_v20260717.gpkg/prodes_amazonia_legal_v20260717.gpkg", layer = "yearly_deforestation")
no_forest_Prodes <- st_read("D:/NextCloudMirror/data/auxiliars/OSM/prodes_amazonia_legal_v20260717.gpkg/prodes_amazonia_legal_v20260717.gpkg", layer = "no_forest")
hydrography_Prodes <- st_read("D:/NextCloudMirror/data/auxiliars/OSM/prodes_amazonia_legal_v20260717.gpkg/prodes_amazonia_legal_v20260717.gpkg", layer = "hydrography")
residual_Prodes <- st_read("D:/NextCloudMirror/data/auxiliars/OSM/prodes_amazonia_legal_v20260717.gpkg/prodes_amazonia_legal_v20260717.gpkg", layer = "residual")

accumulated_deforestation_2007_C51L41 <- st_intersection(accumulated_deforestation_2007, tile_C51L41_s)
yearly_deforestation_C51L41 <- st_intersection(yearly_deforestation, tile_C51L41_s)
no_forest_Prodes_C51L41 <- st_intersection(no_forest_Prodes, tile_C51L41_s)
hydrography_Prodes_C51L41 <- st_intersection(hydrography_Prodes, tile_C51L41_s)
residual_Prodes_C51L41 <- st_intersection(residual_Prodes, tile_C51L41_s)

Prodes_upto2007_C51L41 <- st_transform(accumulated_deforestation_2007_C51L41, 4326)
Prodes_after2007_C51L41 <- st_transform(yearly_deforestation_C51L41, 4326)
Prodes_residual_C51L41 <- st_transform(residual_Prodes_C51L41, 4326)
Prodes_hydro_C51L41 <- st_transform(hydrography_Prodes_C51L41, 4326)
Prodes_noforest_C51L41 <- st_transform(no_forest_Prodes_C51L41, 4326)

# SAD ####
SAD_tile <- read_sf("D:/NextCloudMirror/data/alerts/SAD/SAD_tiled_valid.gpkg")
unique(SAD_tile$CLASS)
SAD_tile |> filter(id=="C51L41") -> SAD_C51L41
SAD_C51L41 <- st_transform(SAD_C51L41, 4326)

# MapBiomas ####
MapBiomas_tile <- read_sf("D:/NextCloudMirror/data/alerts/MapBiomas/MapBiomas_tiled.gpkg")
MapBiomas_tile |> filter(id=="C51L41") -> MapBiomas_C51L41
MapBiomas_C51L41 <- st_transform(MapBiomas_C51L41, 4326)

# DEM ####
# DEM_C51L41_m <- rast("D:/NextCloudMirror/images/dem_C51L41.tif")
# plot(DEM_C51L41_m)
# 
# contours_DEM <- read_sf("Contours_DEM_C51L41.gpkg")
# mapview(contours_DEM)

# OSM ####

st_layers("D:/NextCloudMirror/data/auxiliars/OSM/norte-260804-free.gpkg/norte.gpkg")

OSM_test <- read_sf("D:/NextCloudMirror/data/auxiliars/OSM/norte-260804-free.gpkg/norte.gpkg", 
                    layer="gis_osm_water_a_free")
OSM_water <- st_intersection(OSM_test, tile_C51L41)
unique(OSM_water$fclass)
mapview(OSM_water)

OSM_water |> filter(fclass == "riverbank") -> OSM_riverbank
OSM_water |> filter(fclass != "riverbank") -> OSM_wetland 

OSM_test <- read_sf("D:/NextCloudMirror/data/auxiliars/OSM/norte-260804-free.gpkg/norte.gpkg", 
                    layer="gis_osm_roads_free")
OSM_roads <- st_intersection(OSM_test, tile_C51L41)
unique(OSM_roads$fclass)
mapview(OSM_roads)

OSM_test <- read_sf("D:/NextCloudMirror/data/auxiliars/OSM/norte-260804-free.gpkg/norte.gpkg", 
                    layer="gis_osm_waterways_free")
OSM_river <- st_intersection(OSM_test, tile_C51L41)
unique(OSM_river$fclass)
mapview(OSM_river) # linestring

OSM_test <- read_sf("D:/NextCloudMirror/data/auxiliars/OSM/norte-260804-free.gpkg/norte.gpkg", 
                    layer="gis_osm_buildings_a_free")
OSM_build <- st_intersection(OSM_test, tile_C51L41)
unique(OSM_build$fclass)
mapview(OSM_build)

OSM_test <- read_sf("D:/NextCloudMirror/data/auxiliars/OSM/norte-260804-free.gpkg/norte.gpkg", 
                    layer="gis_osm_landuse_a_free")
OSM_forest <- st_intersection(OSM_test, tile_C51L41)
unique(OSM_forest$fclass)
mapview(OSM_forest)

OSM_others <- st_difference(tile_C51L41, OSM_forest)

OSM_others |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") -> OSM_others

#mapview(OSM_others[69,]) poly 69 need editions QGIS to separe the river
# OSM_others[-c(1:8,28,69),] -> OMS_polys
# OSM_others[69,] -> OMS_69
# write_sf(OMS_69, "OMS_69.gpkg")

OSM_poly69 <- read_sf("D:/NextCloudMirror/data/auxiliars/OSM/OMS_poly_69c.gpkg")
st_geometry(OSM_poly69) <- "geometry"
OSM_poly69 |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geometry)) -> OSM_poly69

mapview(OSM_poly69)

OSM_poly <- rbind(OMS_polys[,c(7:10)], OSM_poly69[,c(7:10)])

# visual separation
# disturbances
# CzQ 1
# CrSv 22-24 28-30 32-35 37 39-41 43 46-48 55 65-66 67most 69-71

# NoForest
OSM_poly[c(3,10,12,13,14,15,16,17,18,20,21,25,26,27,31,38,56,57,58,59,60,61,62,63,64),] -> OSM_poly_NF

# Water
OSM_poly[c(4,6,7,9,42,44,45),] -> OSM_poly_water # 67- maskS2 524

# wetland
OSM_poly[c(2,5,8,11,19,36,49,50,51,52,53,54,68),] -> OSM_poly_wetland
mapview(OSM_poly_wetland, color = "magenta", alpha.regions = 0, lwd = 3, legend = FALSE)



# final version ####

# water ####
OSM_riverbank
st_geometry(OSM_riverbank) <- "geometry"
OSM_riverbank$source <- "OSM_riverbank"
OSM_riverbank[,12]

Prodes_hydro_C51L41
st_geometry(Prodes_hydro_C51L41) <- "geometry"
Prodes_hydro_C51L41$source <- "Prodes_hydrography"
Prodes_hydro_C51L41[,11]

terraClass_C51L41_sf_Water
terraClass_C51L41_sf_Water$source <- "TC2020_water"
terraClass_C51L41_sf_Water[,3]

WORLDCOVER21_C51L41_Water
WORLDCOVER21_C51L41_Water$source <- "WC2021_water"
WORLDCOVER21_C51L41_Water[,3]

polys_IBGE_C51L41
st_geometry(polys_IBGE_C51L41) <- "geometry"
polys_IBGE_C51L41$source <- c("IBGE_lagoaNA", "IBGE_lagoaPavao", "IBGE_RioRoo")
polys_IBGE_C51L41[,33]

GSW_C51L41_water
GSW_C51L41_water$source <- paste0("GSW_recurent")
GSW_C51L41_water[,3]

OSM_poly_water
st_geometry(OSM_poly_water) <- "geometry"
OSM_poly_water$source <- "OSM_Water_visual"
OSM_poly_water[,6]

Water_C51L41 <- bind_rows(OSM_riverbank[,12],
                          Prodes_hydro_C51L41[,11],
                          terraClass_C51L41_sf_Water[,3],
                          WORLDCOVER21_C51L41_Water[,3],
                          polys_IBGE_C51L41[,33],
                          GSW_C51L41_water[,3],
                          OSM_poly_water[,6])

mapview(Water_C51L41)

Water_C51L41_diss <- spatialEco::sf_dissolve(Water_C51L41)
st_geometry(Water_C51L41_diss) <- "geometry"
Water_C51L41_diss$class <- "water"
mapview(Water_C51L41_diss)

write_sf(Water_C51L41_diss, "Water_C51L41_diss.gpkg")

# wetland ####
WORLDCOVER21_C51L41_Wetland
st_geometry(WORLDCOVER21_C51L41_Wetland) <- "geometry"
WORLDCOVER21_C51L41_Wetland$source <- "WC2021_Wetland"
WORLDCOVER21_C51L41_Wetland[,3]

OSM_wetland
st_geometry(OSM_wetland) <- "geometry"
OSM_wetland$source <- "OSM_Wetland"
OSM_wetland[,12]

Wetland_C51L41_25
st_geometry(Wetland_C51L41_25) <- "geometry"
Wetland_C51L41_25$source <- "LBA_Wetland_25"
Wetland_C51L41_25[,3]

OSM_poly_wetland
st_geometry(OSM_poly_wetland) <- "geometry"
OSM_poly_wetland$source <- "OSM_Wetland_symbol"
OSM_poly_wetland[,6]

Wetland_C51L41 <- bind_rows(WORLDCOVER21_C51L41_Wetland[,3],
                            OSM_wetland[,12],
                            Wetland_C51L41_25[,3],
                            OSM_poly_wetland[,6])

mapview(Wetland_C51L41)

Wetland_C51L41_diss <- spatialEco::sf_dissolve(Wetland_C51L41)
st_geometry(Wetland_C51L41_diss) <- "geometry"
Wetland_C51L41_diss$class <- "wetland"
mapview(Wetland_C51L41_diss)

write_sf(Wetland_C51L41_diss, "Wetland_C51L41_diss.gpkg")

# no-forest ####
Prodes_noforest_C51L41
st_geometry(Prodes_noforest_C51L41) <- "geometry"
Prodes_noforest_C51L41$source <- "Prodes_NoForest"
Prodes_noforest_C51L41[,11]

terraClass_C51L41_sf_NF
st_geometry(terraClass_C51L41_sf_NF) <- "geometry"
terraClass_C51L41_sf_NF$source <- "TC2020_NoForest"
terraClass_C51L41_sf_NF[,3]

no_forest_C51L41
st_geometry(no_forest_C51L41) <- "geometry"
no_forest_C51L41$source <- "no_forest"
no_forest_C51L41[,11]

OSM_poly_NF
st_geometry(OSM_poly_NF) <- "geometry"
OSM_poly_NF$source <- "OSM_no_forest_guess"
OSM_poly_NF[,6]

NoForest_C51L41 <- bind_rows(Prodes_noforest_C51L41[,11],
                             terraClass_C51L41_sf_NF[,3],
                             OSM_poly_NF[,6])

mapview(NoForest_C51L41)

NoForest_C51L41_diss <- spatialEco::sf_dissolve(NoForest_C51L41)
st_geometry(NoForest_C51L41_diss) <- "geometry"
NoForest_C51L41_diss$class <- "NoForest"
mapview(NoForest_C51L41_diss)

write_sf(NoForest_C51L41_diss, "NoForest_C51L41_diss.gpkg")


# old deforestation ####
MaskGLADS2_C51L41_FDA <- read_sf("MaskGLADS2_C51L41_FDA.gpkg")

MaskGLADS2_C51L41_FDA |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geom)) -> MaskGLADS2_C51L41_FDA

Prodes_mask_upto19
st_geometry(Prodes_mask_upto19) <- "geometry"
Prodes_mask_upto19$source <- "Prodes_upto2019"
Prodes_mask_upto19[,5]

Mask_MapBiomas_C51L41
st_geometry(Mask_MapBiomas_C51L41) <- "geometry"
Mask_MapBiomas_C51L41$source <- "MapBiomas_upto2019"
Mask_MapBiomas_C51L41[,14]

MaskGLADS2_C51L41_FDA
st_geometry(MaskGLADS2_C51L41_FDA) <- "geometry"
MaskGLADS2_C51L41_FDA$source <- "GladS2_mask2020"
MaskGLADS2_C51L41_FDA[,3]

OldDisturbances_C51L41 <- rbind(Prodes_mask_upto19[,5],
                                Mask_MapBiomas_C51L41[,14],
                                MaskGLADS2_C51L41_FDA[,3])

OldDisturbances_C51L41 |>
  st_make_valid() |>
  st_cast("MULTIPOLYGON") |>
  st_cast("POLYGON") |>
  filter(!st_is_empty(geometry)) -> OldDisturbances_C51L41

mapview(OldDisturbances_C51L41)

OldDisturbances_C51L41_diss <- spatialEco::sf_dissolve(OldDisturbances_C51L41)
st_geometry(OldDisturbances_C51L41_diss) <- "geometry"
OldDisturbances_C51L41_diss$class <- "Old_disturbances"
mapview(OldDisturbances_C51L41_diss)

write_sf(OldDisturbances_C51L41_diss, "OldDisturbances_C51L41_diss.gpkg")

Mask_C51L41_diss <- rbind(OldDisturbances_C51L41_diss,
                          NoForest_C51L41_diss,
                          Water_C51L41_diss,
                          Wetland_C51L41_diss)

unique(Water_C51L41$source)

write_sf(Mask_C51L41_diss, "MaskSources_C51L41_diss.gpkg")

Mask_C51L41 <- rbind(OldDisturbances_C51L41,
                     NoForest_C51L41,
                     Water_C51L41,
                     Wetland_C51L41)

unique(Mask_C51L41$source)

write_sf(Mask_C51L41, "MaskSources_C51L41.gpkg")

# class automatic alerts ####

# centroid extract class ####
Aut_C51L41_sf$idx <- 1:152968

Aut_C51L41_sf |>
  st_centroid(geometry) -> Aut_C51L41_centroid

Aut_C51L41_Classes <- st_join(Aut_C51L41_centroid, Deter20_24_C51L41[,c(3,5)], join = st_intersects)
names(Aut_C51L41_Classes)[1:5] <- c("doy20_aut", "date_aut", "idx", "class_Deter", "date_Deter")

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, Prodes_upto2007_C51L41[,c(3,7)], join = st_intersects)
names(Aut_C51L41_Classes)[6:7] <- c("class_Prodes07", "date_Prodes07")   
Aut_C51L41_Classes$date_Prodes07 <- as.Date("2007-01-01")[1]
Aut_C51L41_Classes$date_Prodes07[is.na(Aut_C51L41_Classes$class_Prodes07)] <- NA

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, Prodes_after2007_C51L41[,c(5,8)], join = st_intersects)
names(Aut_C51L41_Classes)[8:9] <- c("class_Prodes", "date_Prodes")   

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, Prodes_residual_C51L41[,c(3,7)], join = st_intersects)
names(Aut_C51L41_Classes)[10:11] <- c("class_Prodesres", "date_Prodesres") 
Aut_C51L41_Classes$date_Prodesres[!is.na(Aut_C51L41_Classes$date_Prodesres)] <- as.Date("2025-01-01")[1]

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, Prodes_hydro_C51L41[,c(4,7)], join = st_intersects)
names(Aut_C51L41_Classes)[12:13] <- c("class_ProdesHydr", "date_ProdesHydr") 
Aut_C51L41_Classes$date_ProdesHydr <- as.Date("2007-01-01")[1]
Aut_C51L41_Classes$date_ProdesHydr[is.na(Aut_C51L41_Classes$class_ProdesHydr)] <- NA

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, Prodes_noforest_C51L41[,c(4,7)], join = st_intersects)
names(Aut_C51L41_Classes)[14:15] <- c("class_ProdesNF", "date_ProdesNF") 
Aut_C51L41_Classes$date_ProdesNF <- as.Date("2007-01-01")[1]
Aut_C51L41_Classes$date_ProdesNF[is.na(Aut_C51L41_Classes$class_ProdesNF)] <- NA

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, MapBiomas_C51L41[,c(12,8)], join = st_intersects)
names(Aut_C51L41_Classes)[16:17] <- c("class_MapBiomas", "date_MapBiomas")

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, Mask_MapBiomas_C51L41[,c(10,6)], join = st_intersects)
names(Aut_C51L41_Classes)[18:19] <- c("class_MaskMB", "date_MaskMB")

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, SAD_C51L41[,c(1,10)], join = st_intersects)
names(Aut_C51L41_Classes)[20:21] <- c("class_SAD", "date_SAD")

# Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, Mask_SAD_C51L41[,c(1)], join = st_intersects)
# names(Aut_C51L41_Classes)[19:20] <- c("class_MaskSAD", "date_MaskSAD")
# Aut_C51L41_Prodes$date_MaskSAD <- as.Date("2019-01-01")[1]
# Aut_C51L41_Prodes$date_MaskSAD[is.na(Aut_C51L41_Prodes$alerta)] <- NA

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, MaskGLADS2_C51L41_sf[1], join = st_intersects)
names(Aut_C51L41_Classes)[22] <- c("class_MaskGLADS2")
Aut_C51L41_Classes$class_MaskGLADS2[!is.na(Aut_C51L41_Classes$class_MaskGLADS2)] <- "maskGLADS2"
Aut_C51L41_Classes$date_MaskGLADS2 <- as.Date("2020-01-01")[1]
Aut_C51L41_Classes$date_MaskGLADS2[is.na(Aut_C51L41_Classes$class_MaskGLADS2)] <- NA

plot(terraClass_C51L41_sf)
Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, terraClass_C51L41_sf, join = st_intersects)
names(Aut_C51L41_Classes)[24] <- c("class_TC2020")
Aut_C51L41_Classes$date_TC <- as.Date("2020-01-01")[1]
Aut_C51L41_Classes$date_TC[is.na(Aut_C51L41_Classes$class_TC2020)] <- NA

Aut_C51L41_Classes <- st_join(Aut_C51L41_Classes, Mask_C51L41_diss, join = st_intersects)
names(Aut_C51L41_Classes)[26] <- c("class_MasksC")
Aut_C51L41_Classes$date_MasksC <- as.Date("2020-01-01")[1]
Aut_C51L41_Classes$date_MasksC[is.na(Aut_C51L41_Classes$class_MasksC)] <- NA


Aut_C51L41_Classes |> mutate(class_multisource = coalesce(class_Deter,class_Prodes,
                                                          class_Prodes07,class_Prodesres,
                                                          class_MapBiomas, class_SAD,
                                                          class_ProdesNF,class_ProdesHydr,
                                                          class_MasksC,class_MaskMB,
                                                          class_MaskGLADS2, class_TC2020
                                                          )) -> Aut_C51L41_class

Aut_C51L41_class |> mutate(date_multisource = coalesce(date_Deter,date_Prodes,
                                                       date_Prodes07,date_Prodesres,
                                                       date_MapBiomas, date_SAD,
                                                       date_ProdesNF,date_ProdesHydr,
                                                       date_MasksC,date_MaskMB,
                                                       date_MaskGLADS2, date_TC
                                                       )) -> Aut_C51L41_class


Aut_C51L41_sf
Aut_C51L41_centroid
Aut_C51L41_class$idx[duplicated(Aut_C51L41_class$idx)]
16976+152968-169944 

Aut_C51L41_class <- Aut_C51L41_class[,c(3,2,29,30)] %>%
  distinct(geometry, .keep_all = TRUE)

Aut_C51L41_sf |>
  filter(!(idx %in% Aut_C51L41_class$idx))

which(Aut_C51L41_Classes$idx == 97857)
Aut_C51L41_Classes[110320:110322,]
which(Aut_C51L41_class$idx == 97856)

Aut_C51L41_class <- bind_rows(Aut_C51L41_class[1:97856,], 
                              Aut_C51L41_class[97856,],
                              Aut_C51L41_class[97857:152967,])
Aut_C51L41_class[97857,1] <- 97857
# Aut_C51L41_class[97857,2] <- "corte raso com solo exposto"
# Aut_C51L41_class[97857,3] <- as.Date("2023-08-16")[1]
Aut_C51L41_class[97856:97858,]

unique(Aut_C51L41_class$idx == Aut_C51L41_sf$idx)

Aut_C51L41_sf$class_multisource <- Aut_C51L41_class$class_multisource
Aut_C51L41_sf$date_multisource <- Aut_C51L41_class$date_multisource

unique(Aut_C51L41_sf$class_multisource)

unique(MapBiomas_C51L41$CLASS)
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "agriculture" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "MapBiomas_Agric"

unique(Deter20_24_C51L41$CLASS)
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "DESMATAMENTO_CR" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Deter_Def_CrS"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "DESMATAMENTO_VEG" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Deter_Def_CrV"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "CS_DESORDENADO" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Deter_Deg_CsD"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "CS_GEOMETRICO" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Deter_Deg_CsG"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "DEGRADACAO" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Deter_Deg_Cs"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "CICATRIZ_DE_QUEIMADA" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Deter_FireScars_CzQ"

unique(Prodes_noforest_C51L41$class_ProdesNF)
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "nao_floresta2" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_NoForest"

unique(Prodes_hydro_C51L41$class_ProdesHydr)
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "hidrografia" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Water"

unique(Prodes_residual_C51L41$class_Prodesres)
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "RESIDUO" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def_resid"

unique(Prodes_upto2007_C51L41$main_class)
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "DESMATAMENTO" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def_acc2007"

unique(Prodes_after2007_C51L41$class_Prodes)
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "desmatamento por degradação progressiva" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def_degr_progr"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "corte raso com solo exposto" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def_CrS"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "corte raso com vegetação" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def_CrV"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2008"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2009"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2014"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2016"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2017"&
                                  !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2018"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2019"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2020"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "d2021"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "Prodes_Def"

unique(terraClass_C51L41_sf$TC2020)

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "Pasture"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "TC20_Pasture"
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "SecVeg"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "TC20_SecVeg"
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "Water"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "TC20_Water"
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "Deforestation"&
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "TC20_Deforestation"
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "Others"&
                                  !is.na(Aut_C51L41_sf$class_multisource)] <- "TC20_others"

unique(MaskGLADS2_C51L41$MaskS2_ALB)
Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "maskGLADS2" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "GLADS2_mask2020"

unique(SAD_C51L41$CLASS)

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "degradacao" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "SAD_deg"

Aut_C51L41_sf$class_multisource[Aut_C51L41_sf$class_multisource == "desmatamento" &
                                    !is.na(Aut_C51L41_sf$class_multisource)] <- "SAD_def"

unique(Aut_C51L41_sf$class_multisource)

mapview(Aut_C51L41_sf, zcol = "class_multisource", alpha = 0) +
  mapview(tile_C51L41, alpha.regions = 0, lwd = 3, color = "magenta", legend = FALSE)

Aut_C51L41_sf |> filter(is.na(class_multisource)) |>
  mapview(alpha = 0, color = "magenta", legend = FALSE) +
  mapview(tile_C51L41, alpha.regions = 0, lwd = 3, color = "magenta", legend = FALSE)

write_sf(Aut_C51L41_sf, "Aut_C51L41_preclass.gpkg")
