import pandas as pd
import geopandas as gpd

data = pd.read_parquet('../data/raw_data_delays.parquet')
stations_gps = gpd.read_file('../data/spatial_data/stations_gps.shp', encoding='utf-8')

# routes
routes = data['Relacja'].drop_duplicates()\
    .str.split(' - ')\
    .apply(lambda x: sorted(x))\
    .apply(lambda x: ','.join(map(str,x)))\
    .drop_duplicates()\
    .reset_index(drop=True)\
    .to_frame()

routes['Station_A'] = routes['Relacja'].str.split(',').str[0]
routes['Station_B'] = routes['Relacja'].str.split(',').str[1]

routes = routes\
    .merge(stations_gps, how='left', left_on='Station_A', right_on='Stacja')\
    .merge(stations_gps, how='left', left_on='Station_B', right_on='Stacja')\
    .drop(['Stacja_x','Stacja_y'], axis=1)\
    .rename(columns={'geometry_x':'geometry_A', 'geometry_y':'geometry_B'})

geoms = ['geometry_A','geometry_B']
suffixes = ['A', 'B']

for suffix, geom in zip(suffixes, geoms):
    routes[f'lat{suffix}'] = routes[geom].apply(lambda point: point.y)
    routes[f'lon{suffix}'] = routes[geom].apply(lambda point: point.x)

routes.drop(columns=geoms,inplace=True)
routes.to_parquet('../data/routes_empty.parquet', index=False)
routes[['latA','lonA','latB','lonB']].to_csv('../data/coordinates_to_js.csv',index=False)