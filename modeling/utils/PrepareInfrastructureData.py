import osmnx
from shapely.geometry import Polygon, LineString, Point
import geopandas as gpd
from typing import List
import numpy as np

def measure_linestring_distance_inside_polygon(routes_list:List, polygon):
    intersection_lin_str = []
    for route in routes_list:
        inter = route.intersection(polygon)
        intersection_lin_str.append(inter)
        
    route_gdf = gpd.GeoDataFrame(geometry=intersection_lin_str)
    route_gdf.crs = "EPSG:4326"
    route_gdf_projected = route_gdf.to_crs("EPSG:32610")
    total_distance_km = route_gdf_projected.geometry.length.sum() / 1000
    return total_distance_km

def point_inside_polygon(point, polygon):
    """
    Check if a point is inside a polygon using ray casting algorithm.
    """
    x, y = point.coords[0]
    num_intersections = 0
    for i in range(len(polygon.exterior.coords) - 1):
        p1 = polygon.exterior.coords[i]
        p2 = polygon.exterior.coords[i + 1]
        if p1[1] == p2[1]:
            continue
        if min(p1[1], p2[1]) <= y < max(p1[1], p2[1]):
            x_intersect = (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1]) + p1[0]
            if x < x_intersect:
                num_intersections += 1
    return num_intersections % 2 == 1
    

def get_infrastrucute_data_per_area(path_to_shp_file:str, path_to_save_output_file:str):
    shp_file = gpd.read_file(path_to_shp_file, encoding='utf-8')
    #areas_list = shp_file['JPT_NAZWA_'].unique()
    areas_list = shp_file['JPT_KOD_JE'].unique()
    polygon_list = []
    switches_list = []
    level_crossing_list = []
    stations_list = []
    distances_km_list = []
    for area in areas_list:
        polygon = shp_file[shp_file['JPT_KOD_JE']==area]['geometry'].item()

        try:
            railway_features = osmnx.geometries_from_polygon(polygon, tags={'railway': True}).reset_index()

            if 'ref' in railway_features.columns:
                routes = railway_features[(railway_features['element_type']=='way') & (railway_features['railway']=='rail') & (~railway_features['ref'].isna())]['geometry'].tolist()
                switches = railway_features[(railway_features['element_type']=='node') & (railway_features['railway']=='switch') & (~railway_features['ref'].isna())]['geometry'].tolist()
                level_crossing = railway_features[(railway_features['element_type']=='node') & (railway_features['railway']=='level_crossing') & (~railway_features['ref'].isna())]['geometry'].tolist()
            else:
                routes = railway_features[(railway_features['element_type']=='way') & (railway_features['railway']=='rail')]['geometry'].tolist()
                switches = railway_features[(railway_features['element_type']=='node') & (railway_features['railway']=='switch')]['geometry'].tolist()
                level_crossing = railway_features[(railway_features['element_type']=='node') & (railway_features['railway']=='level_crossing')]['geometry'].tolist()
                
            stations = railway_features[(railway_features['element_type']=='node') & (railway_features['railway'].isin(['station', 'halt']))]['geometry'].tolist()
            distance_km = measure_linestring_distance_inside_polygon(routes, polygon)
            
        except ValueError as e:
            switches = []
            level_crossing = [] 
            stations = []
            distance_km = np.nan
            print(e)
            
        polygon_list.append(polygon)
        switches_list.append(len(switches))
        level_crossing_list.append(len(level_crossing))
        stations_list.append(len(stations))
        distances_km_list.append(distance_km)

    gpd_df_out = gpd.GeoDataFrame({
        'area': areas_list,
        'polygon': polygon_list,
        'switches_count': switches_list,
        'level_crossing_count': level_crossing_list,
        'stations_count': stations_list,
        'distance': distances_km_list
    })

    gpd_df_out.to_file(path_to_save_output_file)
