import pandas as pd
import geopandas as gpd
from shapely import Point, LineString
from utils.PreprocessingUtils import convert_to_geometry, create_small_polygon

routes_data = pd.read_parquet('../data/routes_data_all.parquet')
lvl_crossings = gpd.read_file('../data/spatial_data/level_crossings.shp')
switches = gpd.read_file('../data/spatial_data/switches.shp')

# transform source data
routes_data['geometry'] = routes_data['decoded_polylines'].apply(convert_to_geometry)
lvl_crossings['polygon'] = lvl_crossings['geometry'].apply(lambda x: create_small_polygon(x, 0.00001))
switches['polygon'] = switches['geometry'].apply(lambda x: create_small_polygon(x, 0.00001))

# count lvl crossings and switches
keys = routes_data['key'].unique()
dfs_list = []
n = 0

for key in keys:
    n+=1
    temp_df = routes_data[routes_data['key']==key].copy().reset_index(drop=True)
    routes = temp_df['geometry']
    lvl_crossing_count = []
    switches_count = []

    for route in routes:
        lvl_crossing_counter=0
        switches_counter=0
        
        if isinstance(route, Point):
            lvl_crossing_count.append(-1)
            switches_count.append(-1)

        elif isinstance(route, LineString):
            for polygon in lvl_crossings['polygon'].values:
                if route.intersects(polygon):
                    lvl_crossing_counter+=1
            lvl_crossing_count.append(lvl_crossing_counter)

            for polygon in switches['polygon'].values:
                if route.intersects(polygon):
                    switches_counter+=1
            switches_count.append(switches_counter)

    temp_df['level_crossing_count'] = lvl_crossing_count
    temp_df['switches_count'] = switches_count

    dfs_list.append(temp_df)
    print(n/len(keys))

dfs = pd.concat(dfs_list, ignore_index=False)