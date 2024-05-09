import pandas as pd
import geopandas as gpd
import osmnx as ox
from utils.PrepareInfrastructureData import measure_linestring_distance_inside_polygon, point_inside_polygon
import warnings 
warnings.filterwarnings('ignore')

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

# ### join infrastructure data for areas - railway route length

# #### gminy
gminy_kod = joined_wojwwodztwa_powiaty_gminy[~joined_wojwwodztwa_powiaty_gminy['id_gmina'].isna()].reset_index(drop=True)['id_gmina'].unique()
routes_length_within = []
stations_odometer = []
level_crossing_odometer = []
switches_odometer = []

for code in gminy_kod:
    
    try:
        polygon = gminy[gminy['JPT_KOD_JE']==code]['geometry'].item()
        railway_features = ox.geometries_from_polygon(polygon, tags={'railway': True}).reset_index()

        routes = railway_features[(railway_features['element_type']=='way') & (railway_features['railway']=='rail') & (~railway_features['ref'].isna())]['geometry'].tolist()
        switches = railway_features[(railway_features['element_type']=='node') & (railway_features['railway']=='switch') & (~railway_features['ref'].isna())]['geometry'].tolist()
        level_crossing = railway_features[(railway_features['element_type']=='node') & (railway_features['railway']=='level_crossing') & (~railway_features['ref'].isna())]['geometry'].tolist() 
        stations = railway_features[(railway_features['element_type']=='node') & (railway_features['railway'].isin(['station', 'halt']))]['geometry'].tolist() 

        stations_odometer.append(len(stations))
        level_crossing_odometer.append(len(level_crossing))
        switches_odometer.append(len(switches))

        total_distance_within_polygon = measure_linestring_distance_inside_polygon(routes, polygon)
        routes_length_within.append(total_distance_within_polygon)

    except (KeyError, ValueError) as e:
        print(f'{code} - {e}')
        stations_odometer.append(-1)
        level_crossing_odometer.append(-1)
        switches_odometer.append(-1)
        routes_length_within.append(-1)
        continue


gminy_railway_data = pd.DataFrame({
    'id_gmina': gminy_kod,
    'railway_distance_gmina': routes_length_within,
    'stations_odometer_gmina': stations_odometer,
    'level_crossing_odometer_gmina': level_crossing_odometer,
    'switches_odometer_gmina': switches_odometer
})

 
# #### powiaty
powiaty_kod = joined_wojwwodztwa_powiaty_gminy[~joined_wojwwodztwa_powiaty_gminy['id_powiat'].isna()].reset_index(drop=True)['id_powiat'].unique()
routes_length_within = []
stations_odometer = []
level_crossing_odometer = []
switches_odometer = []

for code in powiaty_kod:
    
    try:
        polygon = powiaty[powiaty['JPT_KOD_JE']==code]['geometry'].item()
        railway_features = ox.geometries_from_polygon(polygon, tags={'railway': True}).reset_index()

        routes = railway_features[(railway_features['element_type']=='way') & (railway_features['railway']=='rail') & (~railway_features['ref'].isna())]['geometry'].tolist()
        switches = railway_features[(railway_features['element_type']=='node') & (railway_features['railway']=='switch') & (~railway_features['ref'].isna())]['geometry'].tolist()
        level_crossing = railway_features[(railway_features['element_type']=='node') & (railway_features['railway']=='level_crossing') & (~railway_features['ref'].isna())]['geometry'].tolist() 
        stations = railway_features[(railway_features['element_type']=='node') & (railway_features['railway'].isin(['station', 'halt']))]['geometry'].tolist() 

        stations_odometer.append(len(stations))
        level_crossing_odometer.append(len(level_crossing))
        switches_odometer.append(len(switches))

        total_distance_within_polygon = measure_linestring_distance_inside_polygon(routes, polygon)
        routes_length_within.append(total_distance_within_polygon)

    except (KeyError, ValueError) as e:
        print(f'{code} - {e}')
        stations_odometer.append(-1)
        level_crossing_odometer.append(-1)
        switches_odometer.append(-1)
        routes_length_within.append(-1)
        continue

powiaty_railway_data = pd.DataFrame({
    'id_powiat': powiaty_kod,
    'railway_distance_powiat': routes_length_within,
    'stations_odometer_powiat': stations_odometer,
    'level_crossing_odometer_powiat': level_crossing_odometer,
    'switches_odometer_powiat': switches_odometer
})

# join data
joined_wojwwodztwa_powiaty_gminy = joined_wojwwodztwa_powiaty_gminy.merge(gminy_railway_data, how='left', on='id_gmina').merge(powiaty_railway_data, how='left', on='id_powiat')

# save spatial data
joined_wojwwodztwa_powiaty_gminy.to_file('../data/spatial_data/joined_wojwwodztwa_powiaty_gminy0905.shp', encoding='utf-8', index=False)

# save parquet data
joined_wojwwodztwa_powiaty_gminy['lat'] = joined_wojwwodztwa_powiaty_gminy.apply(lambda row: row['geometry'].y, axis=1)
joined_wojwwodztwa_powiaty_gminy['lon'] = joined_wojwwodztwa_powiaty_gminy.apply(lambda row: row['geometry'].x, axis=1)
joined_wojwwodztwa_powiaty_gminy.drop('geometry', axis=1, inplace=True)

joined_wojwwodztwa_powiaty_gminy.to_parquet('../data/joined_wojwwodztwa_powiaty_gminy0905.parquet', index=False)