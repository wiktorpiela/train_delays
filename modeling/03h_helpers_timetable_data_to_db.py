import pandas as pd
import geopandas as gpd

data = pd.read_parquet('../data/final_data_to_modeling1105.parquet')

timetable = data[['key','Stacja', 'arrival_on_time', 'departure_on_time']].drop_duplicates()
timetable['arrival_time'] = timetable['arrival_on_time'].dt.time
timetable['departure_time'] = timetable['departure_on_time'].dt.time
timetable  = timetable[['key','Stacja','arrival_time', 'departure_time']].drop_duplicates()

stations = gpd.read_file('../data/spatial_data/stations_gps_crs_4326_utf8.shp')
stations['station_id'] = stations.index + 1

rel = pd.read_parquet('../data/routes_data_complete_1804.parquet')
rel = rel[['key']].drop_duplicates().reset_index(drop=True)
rel['route_id'] = rel.index + 1

timetable = timetable.merge(rel, how='left', on='key').merge(stations.drop('geometry', axis=1), how='left', on='Stacja')

timetable_final = timetable[['route_id', 'station_id', 'arrival_time', 'departure_time']]

timetable_final.to_csv('../data/timetable_data_to_db.csv', index=False)