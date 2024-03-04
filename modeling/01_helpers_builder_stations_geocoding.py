import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from utils.GeneralUtils import osm_geocoder, google_maps_geocoder

data = pd.read_parquet('../data/raw_data_delays.parquet')
stations = data['Stacja'].unique()

stations_geocoded = osm_geocoder(stations)
no_gps = stations_geocoded[(stations_geocoded['lat']==-1) | (stations_geocoded['lon']==-1)]

if len(no_gps) > 0:
    no_found_stations = no_gps['Stacja'].unique()
    google_geocoded = google_maps_geocoder(no_found_stations)
    stations_geocoded = pd.concat([stations_geocoded, google_geocoded], ignore_index=True)

stations_geocoded['geometry'] = df.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
gdf = gpd.GeoDataFrame(df, geometry='geometry')
gdf.to_file('../data/spatial_data/stations_gps.shp')

