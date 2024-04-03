import pandas as pd
import numpy as np
import geopandas as gpd
import utils.PreprocessingUtils as utils

# load data
data = pd.read_parquet('../data/raw_data_delays.parquet')
stations_gps = gpd.read_file('../data/spatial_data/stations_gps.shp', encoding='utf-8')

# prepare raw data and join stations gps
data = utils.prepare_raw_data(data)
data = pd.merge(data, stations_gps, on='Stacja', how='left')

data['lat'] = data['geometry'].apply(lambda row: row.y)
data['lon'] = data['geometry'].apply(lambda row: row.x)
data.drop('geometry', axis=1, inplace=True)

# station count
data['station_count_on_curr_station'] = data.groupby(['pk', 'Relacja']).cumcount()
data['full_route_station_count'] = data.groupby(['pk', 'Relacja'])['Relacja'].transform('count')

# get routes info
idxs = [i for i in range(5)]
idxs.append(7)
routes_data = pd.read_parquet('../data/routes_data_all.parquet').iloc[:, idxs]

dfs_out = []
pks = data['pk'].unique()

for pk in pks:
    temp_df = data[data['pk']==pk].copy().reset_index(drop=True)

    key1 = temp_df.groupby('Relacja')['Stacja'].agg(utils.unique_list_preserve_order).index.item()
    key2 = ', '.join(temp_df.groupby('Relacja')['Stacja'].agg(utils.unique_list_preserve_order)[0])
    key = f'{key1}_{key2}'
    temp_df['key'] = key

    temp_df = temp_df.merge(routes_data, how='left', on=['key', 'Relacja', 'Stacja', 'lat', 'lon'])
    temp_df.drop('key', axis=1, inplace=True)

    dfs_out.append(temp_df)
