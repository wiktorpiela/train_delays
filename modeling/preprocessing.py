import pandas as pd
import numpy as np
import geopandas as gpd
import utils.PreprocessingUtils as utils
from haversine import haversine, Unit
from shapely.geometry import Point


# #### load data


data = pd.read_parquet('../data/raw_data_delays.parquet')
stations_gps = gpd.read_file('../data/spatial_data/stations_gps.shp', encoding='utf-8')


# #### prepare raw data and join stations gps


data = utils.prepare_raw_data(data)
data = pd.merge(data, stations_gps, on='Stacja', how='left')


data = utils.geometry_point_to_lat_lon(data)


# ### station count
# <ul>
#     <li>full route station count</li>
#     <li>station count on current station</li>
# </ul>


data['station_count_on_curr_station'] = data.groupby(['pk', 'Relacja']).cumcount()
# data['full_route_station_count'] = data.groupby(['pk', 'Relacja'])['Relacja'].transform('count')


# #### get routes info


routes_data = pd.read_parquet('../data/routes_data_complete_1804.parquet')
routes_data.drop(['encoded_polylines'], axis=1, inplace=True)


dfs_out = []
pks = data['pk'].unique()

for pk in pks:
    temp_df = data[data['pk']==pk].copy().reset_index(drop=True)

    key1 = temp_df.groupby('Relacja')['Stacja'].agg(utils.unique_list_preserve_order).index.item()
    key2 = ', '.join(temp_df.groupby('Relacja')['Stacja'].agg(utils.unique_list_preserve_order)[0])
    key = f'{key1}_{key2}'
    temp_df['key'] = key

    temp_df['prev_stations'] = temp_df['Stacja'].shift(1)
    temp_df['next_stations'] = temp_df['Stacja'].shift(-1)

    temp_df_merged = temp_df.merge(routes_data, how='left', on=['key','Relacja', 'Stacja', 'lat', 'lon', 'prev_stations', 'next_stations'])
    dfs_out.append(temp_df_merged)

df_out = pd.concat(dfs_out, ignore_index=True)


keys_to_remove = df_out[df_out['distances'].isna()]['key'].unique()
df_out = df_out[~df_out['key'].isin(keys_to_remove)].reset_index(drop=True)


# ### distances
# <ul>
#     <li>distance distance until current station</li>
#     <li>distance from start station</li>
#     <li>distance to final station</li>
#     <li>distance distance from the nearest big city station</li>
# </ul>


df_out['cumsum_distances'] = df_out.groupby('pk')['distances'].cumsum()


dfs_out = []
pks = df_out['pk'].unique()

for pk in pks:
    temp_df = df_out[df_out['pk']==pk].copy().reset_index(drop=True)
    temp_df['distance_to_finish'] = np.array(temp_df['cumsum_distances'].iloc[::-1])
    dfs_out.append(temp_df)
    
df_out = pd.concat(dfs_out, ignore_index=True)


big_city_names = pd.read_csv('../data/big_cities_dict.csv', sep=';').iloc[:,0].values
big_city_stations = stations_gps[stations_gps['Stacja'].isin(big_city_names)].reset_index(drop=True)
big_city_stations = utils.geometry_point_to_lat_lon(big_city_stations)


distances = []
for _, row1 in df_out.iterrows():
    min_distance = np.inf
    for _, row2 in big_city_stations.iterrows():
        distance = haversine((row1['lat'], row1['lon']), (row2['lat'], row2['lon']), unit=Unit.KILOMETERS)
        min_distance = min(min_distance, distance)
    distances.append(min_distance)

df_out['nearest_big_city_distance'] = distances


df_out[['distances', 'cumsum_distances', 'distance_to_finish']] = df_out[['distances', 'cumsum_distances', 'distance_to_finish']].apply(lambda x: x / 1000)


# ### weather data


weather = pd.read_parquet('../data/weather_data.parquet')
weather.drop(columns=['stations','source','tzoffset','datetimeEpoch'], inplace=True)
weather['datetime_merge'] = pd.to_datetime(weather['date'].astype(str) + ' ' + weather['datetime'].astype(str))


df_out['datetime_merge'] = df_out['arrival_on_time'].dt.floor('H')


df_out_merged = pd.merge(
    df_out,
    weather,
    how='left',
    on=['lat', 'lon', 'datetime_merge']
).drop(columns=['date','datetime_merge', 'datetime'])


### fixing weather cols

#### snow, windgust, visibility, solarradiation, solarenergy, uvindex
cols_to_fix = ['snow','windgust','visibility','solarradiation','solarenergy','uvindex']
for col in cols_to_fix:
    df_out_merged[col] = df_out_merged[col].fillna(-1)

#### preciptype
df_out_merged['preciptype'] = df_out_merged['preciptype'].fillna('None')
df_out_merged['preciptype'] = df_out_merged['preciptype'].apply(lambda x: '_'.join(map(str, x)) if isinstance(x, np.ndarray) else x)
preciptype_dummies = pd.get_dummies(df_out_merged['preciptype'], prefix='preciptype', dtype=float)
df_out_merged = pd.concat([df_out_merged.drop('preciptype', axis=1), preciptype_dummies], axis=1)

#### conditions
df_out_merged['conditions'] = df_out_merged['conditions'].str.replace(', ', '_').str.replace(',', '_').str.replace(' ', '_')
condition_dummies = pd.get_dummies(df_out_merged['conditions'], dtype=float, prefix="conditions")
df_out_merged = pd.concat([df_out_merged.drop('conditions', axis=1), condition_dummies], axis=1)

#### icon
icon_dummies = pd.get_dummies(df_out_merged['icon'], dtype=float, prefix="icon")
df_out_merged = pd.concat([df_out_merged.drop('icon', axis=1), icon_dummies], axis=1)


# ### longer stop duration


df_out_merged['stop_duration'] = (df_out_merged['departure_on_time'] - df_out_merged['arrival_on_time']).dt.total_seconds()/60
for i in range(1, 7):
    df_out_merged[f'stop_duration_lag{i}'] = df_out_merged.groupby(['pk','Relacja'])['stop_duration'].transform(lambda x: x.shift(i))
    df_out_merged[f'stop_duration_lag{i}'] = df_out_merged[f'stop_duration_lag{i}'].fillna(-1)


# ### date features and holidays


cols = ['arrival_on_time','departure_on_time']
for col in cols:
    df_out_merged = utils.fix_dates(df_out_merged, col)
    
df_out_merged = utils.apply_date_features(df_out_merged)


# checkpoint = df_out_merged.copy()


# ### join polish administrative units data


administrative_units = pd.read_parquet('../data/joined_wojewodztwa_powiaty_gminy.parquet')


df_out_merged_joined_administrative_units = pd.merge(df_out_merged, administrative_units, how='left', on=['Stacja', 'lat', 'lon'])

cols = ['id_gmina', 'id_powiat']
for col in cols:
    df_out_merged_joined_administrative_units[col] = df_out_merged_joined_administrative_units[col].fillna(-1)
    df_out_merged_joined_administrative_units[col] = df_out_merged_joined_administrative_units[col].astype(int)


# #### join gus data


gus_data_gminy = pd.read_csv('../data/gminy.csv', sep=';')[['id_gmina','powierdzchnia_km2', 'Ludność ogółem\r\n Population', 'gestośc zaludnienia na 1 km2']]
gus_data_powiaty = pd.read_csv('../data/powiaty.csv', sep=';')[['id_powiat','Powierzchnia w km2\r\nArea','Ludność ogółem\r\n Population', 'ludnosc_na_1_km2']]


final_data = df_out_merged_joined_administrative_units\
    .merge(gus_data_gminy, how='left', on='id_gmina')\
    .merge(gus_data_powiaty, how='left', on='id_powiat')


final_data.to_parquet('../data/final_data_to_modeling0805.parquet', index=False)

