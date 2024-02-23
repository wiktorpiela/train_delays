import pandas as pd
import numpy as np
import utils.PreprocessingUtils as utils

data = pd.read_parquet('../data/raw_data_delays.parquet')
gps = pd.read_csv('../data/station_gps.csv')

# select only specific routes
data = utils.get_specific_routes(data, 1000)

data = utils.prepare_raw_data(data)
data = pd.merge(data, gps, on='Stacja', how='left')

### station count
    # full route station count
    # station count on current station
data['station_count_on_curr_station'] = data.groupby(['pk', 'Relacja']).cumcount()
data['full_route_station_count'] = data.groupby(['pk', 'Relacja'])['Relacja'].transform('count')

### distances
    # full route distance
    # distance distance until current station
    # distance from start station
    # distance to final station
    # distance distance from the nearest big city station
data = utils.count_distances(data, gps, '../data/big_cities_dict.csv')

### date features and holidays
cols = ['arrival_on_time','departure_on_time']
for col in cols:
    data = utils.fix_dates(data, col)
    
data = utils.apply_date_features(data)

### longer stop duration
data['stop_duration'] = (data['departure_on_time'] - data['arrival_on_time']).dt.total_seconds()/60
for i in range(1, 7):
    data[f'stop_duration_lag{i}'] = data.groupby(['pk','Relacja'])['stop_duration'].transform(lambda x: x.shift(i))
    data[f'stop_duration_lag{i}'] = data[f'stop_duration_lag{i}'].fillna(-1)
    
### apply weather data
weather = pd.read_parquet('../data/weather_data.parquet')
weather.drop(columns=['stations','source','tzoffset','datetimeEpoch'], inplace=True)
weather['datetime_merge'] = pd.to_datetime(weather['date'].astype(str) + ' ' + weather['datetime'].astype(str))

data['datetime_merge'] = data['arrival_on_time'].dt.floor('H')

data = pd.merge(
    data,
    weather,
    how='left',
    on=['lat', 'lon', 'datetime_merge']
).drop(columns=['date','datetime_merge', 'datetime'])

### fixing weather cols
#### snow, windgust, visibility, solarradiation, solarenergy, uvindex
# cols_to_fix = ['snow','windgust','visibility','solarradiation','solarenergy','uvindex']
# for col in cols_to_fix:
#     data[col] = data[col].fillna(-1)

#### preciptype
data['preciptype'] = data['preciptype'].fillna('None')
data['preciptype'] = data['preciptype'].apply(lambda x: '_'.join(map(str, x)) if isinstance(x, np.ndarray) else x)
# preciptype_dummies = pd.get_dummies(data['preciptype'], prefix='preciptype', dtype=float)
# data = pd.concat([data.drop('preciptype', axis=1), preciptype_dummies], axis=1)

#### conditions
data['conditions'] = data['conditions'].str.replace(', ', '_').str.replace(',', '_').str.replace(' ', '_')
# condition_dummies = pd.get_dummies(data['conditions'], dtype=float, prefix="conditions")
# data = pd.concat([data.drop('conditions', axis=1), condition_dummies], axis=1)

#### icon
# icon_dummies = pd.get_dummies(data['icon'], dtype=float, prefix="icon")
# data = pd.concat([data.drop('icon', axis=1), icon_dummies], axis=1)

# save data
data.to_parquet('../data/prepared_data_with_weather.parquet')