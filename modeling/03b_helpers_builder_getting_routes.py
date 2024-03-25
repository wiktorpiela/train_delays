import pandas as pd
import geopandas as gpd
import numpy as np
from utils.GeneralUtils import get_route_attributes
from utils.PreprocessingUtils import unique_list_preserve_order, polylines_decoder
from haversine import haversine, Unit

data = pd.read_parquet('../data/raw_data_delays.parquet')
stations_gps = gpd.read_file('../data/spatial_data/stations_gps.shp', encoding='utf-8')

data['full_route_station_count'] = data.groupby(['pk', 'Relacja'])['Relacja'].transform('count')
data = data.drop_duplicates()

data = data.groupby(['Relacja','full_route_station_count'])['Stacja'].agg(unique_list_preserve_order).reset_index()
data['Stacja'] = data['Stacja'].apply(lambda row: ', '.join(row))
data['key'] = data['Relacja'].map(str) + '_' + data['Stacja'].map(str)
data['Stacja'] = data['Stacja'].apply(lambda row: row.split(', '))
data = data.explode('Stacja')[['key','Relacja','Stacja']].drop_duplicates().reset_index(drop=True)

new_df = data.merge(stations_gps, how='left', on='Stacja')
new_df['lat'] = new_df['geometry'].apply(lambda row: row.y)
new_df['lon'] = new_df['geometry'].apply(lambda row: row.x)

relations = new_df['key'].unique()

df_out_list = []
linestring_list = []
n=0

for rel in relations:
    print(n/len(relations)*100)
    temp_df = new_df[new_df['key']==rel].copy().reset_index(drop=True)

    temp_df['prev_stations'], temp_df['next_stations'], temp_df['distances'], temp_df['durations'], temp_df['encoded_polylines'] = np.full(5, None)

    for i in temp_df.index:
        curr_lat = temp_df.loc[i, 'lat']
        curr_lon = temp_df.loc[i, 'lon']

        try:
            prev_lat = temp_df.loc[i-1, 'lat']
            prev_lon = temp_df.loc[i-1, 'lon']
        except (ValueError, KeyError, IndexError):
            prev_lat, prev_lon = np.full(2, np.nan)
        
        if i == 0:
            distance, duration,  = (0.0,)*2
            encoded_polyline = np.nan
        else:
            distance, duration, encoded_polyline = get_route_attributes(prev_lat, prev_lon, curr_lat, curr_lon)   # f'test{i}', f'test{i}', f'test{i}'

        # if route not found - calculate haversine distance
        if pd.isnull(distance):
            disctance = haversine((prev_lat, prev_lon), (curr_lat, curr_lon), unit=Unit.METERS)

        temp_df.at[i, 'distances'] = distance
        temp_df.at[i, 'durations'] = duration
        temp_df.at[i, 'encoded_polylines'] = encoded_polyline

    temp_df['prev_stations'] = temp_df['Stacja'].shift(1)
    temp_df['next_stations'] = temp_df['Stacja'].shift(-1)

    temp_df.replace({None:np.nan}, inplace=True)

    temp_df, temp_line = polylines_decoder(temp_df)
    linestring_list.append(temp_line)

    df_out_list.append(temp_df)
    n+=1

routes_linestrings = gpd.GeoDataFrame({
    'route_name': relations,
    'geometry':linestring_list
})
routes_linestrings.to_file('../data/routes_linestrings.shp', encoding='utf-8', index=False)

routes_data = pd.concat(df_out_list, ignore_index=True)
routes_data.to_parquet('../data/routes_data_all.parquet', index=False)

