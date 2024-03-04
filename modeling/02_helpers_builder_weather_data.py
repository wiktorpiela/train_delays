import pandas as pd
import geopandas as gpd
from utils.GeneralUtils import get_historical_weather

data = pd.read_parquet('../data/raw_data_delays.parquet')
stations_gps = gpd.read_file('../data/spatial_data/stations.shp')

data = data.merge(stations_gps, how='left', on='Stacja')[['geometry', 'Data']].drop_duplicates()
data['lat'] = data['geometry'].apply(lambda point: point.y)
data['lon'] = data['geometry'].apply(lambda point: point.x)

data = data.drop('geometry', axis=1).rename(columns={'Data':'date'}).drop_duplicates()
weather_data = get_historical_weather(data)
weather_data.to_parquet('../data/weather_data.parquet')