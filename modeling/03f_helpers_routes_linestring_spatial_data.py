import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

def list_of_lists_to_tuples(lst):
    return [tuple(coord) for coord in lst]

routes_data = pd.read_parquet('../data/routes_data_complete_1804.parquet')

rel = routes_data[['key', 'decoded_polylines']]
rel['decoded_polylines'] = rel['decoded_polylines'].apply(list_of_lists_to_tuples)
rel = rel.groupby('key')['decoded_polylines'].apply(lambda x: [item for sublist in x for item in sublist]).reset_index()
rel['decoded_polylines'] = rel['decoded_polylines'].apply(LineString)
rel.rename(columns={'decoded_polylines':'geometry'},inplace=True)

rel = gpd.GeoDataFrame(rel)
rel.crs = 4326

rel = rel.groupby('key').first().reset_index().rename(columns={'key':'route_name'}) # preserve duplicates
rel.to_file('../data/spatial_data/routes.shp', encoding='utf-8', index=False)