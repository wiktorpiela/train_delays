import pandas as pd
import geopandas as gpd

data = pd.read_parquet('../data/raw_data_delays.parquet')
stations_gps = gpd.read_file('../data/spatial_data/stations_gps.shp', encoding='utf-8')
data = pd.merge(data, stations_gps, on='Stacja', how='left')

poland_borders = gpd.read_file('../data/spatial_data/A00_Granice_panstwa.shp', encoding='utf-8')
wojewodztwa = gpd.read_file('../data/spatial_data/A01_Granice_wojewodztw.shp', encoding='utf-8')
powiaty = gpd.read_file('../data/spatial_data/A02_Granice_powiatow.shp', encoding='utf-8')
gminy = gpd.read_file('../data/spatial_data/A03_Granice_gmin.shp', encoding='utf-8')

stations_gps_df = data[['Stacja','geometry']].drop_duplicates().reset_index(drop=True)

# ### check if station is in poland
poland_borders = poland_borders.to_crs('EPSG:4326')
stations_gps_df['in_poland'] = stations_gps_df['geometry'].apply(lambda x: any(x.intersects(poly) for poly in poland_borders['geometry']))

# #### join other kind of areas
joined_wojwwodztwa = gpd.sjoin(gpd.GeoDataFrame(stations_gps_df), wojewodztwa[['geometry', 'JPT_NAZWA_','JPT_KOD_JE']], how="left", op="within").drop('index_right', axis=1)
joined_wojwwodztwa.rename(columns={'JPT_KOD_JE':'id_wojewodztwo', 'JPT_NAZWA_':'nazwa_wojewodztwo'}, inplace=True)

joined_wojwwodztwa_powiaty = gpd.sjoin(joined_wojwwodztwa, powiaty[['geometry', 'JPT_NAZWA_','JPT_KOD_JE']], how="left", op="within").drop('index_right', axis=1)
joined_wojwwodztwa_powiaty.rename(columns={'JPT_KOD_JE':'id_powiat', 'JPT_NAZWA_':'nazwa_powiat'}, inplace=True)

joined_wojwwodztwa_powiaty_gminy = gpd.sjoin(joined_wojwwodztwa_powiaty, gminy[['geometry', 'JPT_NAZWA_','JPT_KOD_JE']], how="left", op="within").drop('index_right', axis=1)
joined_wojwwodztwa_powiaty_gminy.rename(columns={'JPT_KOD_JE':'id_gmina', 'JPT_NAZWA_':'nazwa_gmina'}, inplace=True)

### save spatial file
joined_wojwwodztwa_powiaty_gminy.to_file('../data/spatial_data/joined_wojwwodztwa_powiaty_gminy.shp', encoding='utf-8', index=False)

### save parquet file
joined_wojwwodztwa_powiaty_gminy['lat'] = joined_wojwwodztwa_powiaty_gminy.apply(lambda row: row['geometry'].y, axis=1)
joined_wojwwodztwa_powiaty_gminy['lon'] = joined_wojwwodztwa_powiaty_gminy.apply(lambda row: row['geometry'].x, axis=1)
joined_wojwwodztwa_powiaty_gminy.drop('geometry', axis=1, inplace=True)

joined_wojwwodztwa_powiaty_gminy.to_parquet('../data/joined_wojwwodztwa_powiaty_gminy.parquet', index=False)


