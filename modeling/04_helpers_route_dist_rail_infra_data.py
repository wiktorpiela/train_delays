import pandas as pd
import geopandas as gpd

data = pd.read_parquet('../data/raw_data_delays.parquet')
stations_gps = gpd.read_file('../data/spatial_data/stations_gps.shp', encoding='utf-8')

# railway infrastructure data
platforms = gpd.read_file('../data/spatial_data/platforms.shp', encoding='utf-8')['geometry']
switches = gpd.read_file('../data/spatial_data/switches.shp', encoding='utf-8')['geometry']
level_crossings = gpd.read_file('../data/spatial_data/level_crossings.shp', encoding='utf-8')['geometry']

routes_stations = data[['Relacja', 'Stacja']].groupby('Relacja')['Stacja'].agg(list).reset_index()
routes_stations['Stacja'] = routes_stations['Stacja'].apply(lambda x: ','.join(map(str, x)))
routes_stations['Stacja'] = routes_stations['Stacja'].str.split(',')
routes_stations = routes_stations.explode('Stacja').drop_duplicates()
routes_stations = routes_stations.merge(stations_gps, how='left', on='Stacja')

routes = routes_stations['Relacja'].unique()

for route in routes:
    temp_df = routes_stations[routes_stations['Relacja']==route].copy().reset_index(drop=True)