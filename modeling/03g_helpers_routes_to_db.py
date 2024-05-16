import geopandas as gpd
import pandas as pd

stations = gpd.read_file('../data/spatial_data/stations_gps_crs_4326_utf8.shp')
rel = pd.read_parquet('../data/routes_data_complete_1804.parquet')

rel = rel.groupby('key')['Stacja'].agg(list).reset_index()
rel.insert(0, 'id', rel.index+1)
rel['key'] = rel['key'].apply(lambda row: row.split('_')[0])

rel = rel.explode('Stacja')

stations.insert(0, 'id', stations.index+1)

outdf = pd.merge(rel, stations[['id','Stacja']], how='left', on='Stacja').rename(columns={'id_x':'relation', 'id_y':'station'})[['relation','station']]

outdf.to_csv('../data/routes_to_db.csv', index=False)