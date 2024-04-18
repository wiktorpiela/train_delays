import pandas as pd
import numpy as np
from haversine import haversine, Unit
import polyline
from shapely.geometry import Point, LineString
import geopandas as gpd
import warnings
from itertools import chain
from typing import List
warnings.filterwarnings("ignore")

def flat_list(two_dim_list:List):
    one_d_list = list(chain(*two_dim_list))
    return one_d_list

def unique_list_preserve_order(x):
    seen = set()
    unique_items = []
    for item in x:
        if item not in seen:
            unique_items.append(item)
            seen.add(item)
    return unique_items

def polylines_decoder(df:pd.DataFrame):
    df['decoded_polylines'] = df.apply(lambda row: [(row['lon'], row['lat'])] if row['encoded_polylines'] is None else polyline.decode(row['encoded_polylines'], geojson=True), axis=1)
    decoded_polylines_list = df['decoded_polylines'].to_list()
    decoded_polylines_list_flat = flat_list(decoded_polylines_list)
    route_linestring = LineString(decoded_polylines_list_flat)
    return df, route_linestring

def prepare_raw_data(df:pd.DataFrame):
    df['Przyjazd planowy'] = np.where(df['Przyjazd planowy'].isnull(), df['Odjazd planowy'], df['Przyjazd planowy'])
    df['Odjazd planowy'] = np.where(df['Odjazd planowy'].isnull(), df['Przyjazd planowy'], df['Odjazd planowy'])

    df['Data'] = pd.to_datetime(df['Data'], format='%d.%m.%Y')
    df['Przyjazd planowy'] = pd.to_datetime(df['Przyjazd planowy'], format='%H:%M:%S').dt.time
    df['Odjazd planowy'] = pd.to_datetime(df['Odjazd planowy'], format='%H:%M:%S').dt.time

    df['arrival_on_time'] = pd.to_datetime(df['Data'].astype(str) + ' ' + df['Przyjazd planowy'].astype(str))
    df['departure_on_time'] = pd.to_datetime(df['Data'].astype(str) + ' ' + df['Odjazd planowy'].astype(str))

    for col in ["Opóźnienie przyjazdu", "Opóźnienie odjazdu"]:
        df[col] = df[col].str.replace("min", "")
        df[col] = df[col].str.replace("---", "0")
        df[col] = df[col].str.strip()
        df[col] = pd.to_numeric(df[col])

    df['Numer pociągu'] = df['Numer pociągu'].str.split().str[0]

    train_type_mapping = {
        'ECE': 'EuroCity',
        'EIE': 'Intercity', 'EIJ': 'Intercity',
        'ENE': 'EuroNight',
        'MHE': 'InterVoivodeshipExpressHotel', 'MHS': 'InterVoivodeshipExpressHotel',
        'MME': 'InternationalExpress', 'MMM': 'InternationalExpress',
        'MOE': 'InterVoivodeshipStopping', 'MOJ': 'InterVoivodeshipStopping', 'MOM': 'InterVoivodeshipStopping',
        'MPE': 'InterVoivodeshipExpress', 'MPJ': 'InterVoivodeshipExpress', 'MPM': 'InterVoivodeshipExpress', 'MPS': 'InterVoivodeshipExpress',
        'RAJ': 'LocalAglomeration', 'RAM': 'LocalAglomeration',
        'RMJ': 'LocalInternational', 'RMM': 'LocalInternational',
        'ROE': 'LocalDomestic', 'ROJ': 'LocalDomestic', 'ROM': 'LocalDomestic', 'ROS': 'LocalDomestic',
        'RPE': 'LocalDomesticExpress', 'RPJ': 'LocalDomesticExpress', 'RPM': 'LocalDomesticExpress', 'RPS': 'LocalDomesticExpress'
    }

    traction_type_electric = ['ECE', 'EIE', 'EIJ', 'ENE', 'MHE', 'MME', 'MOE', 'MOJ', 'MPE', 'MPJ', 'RAJ', 'RMJ', 'ROE', 'ROJ', 'RPE']
    traction_type_combustion = ['MHS', 'MMM', 'MOM', 'MPM', 'MPS', 'RAM', 'RMM', 'ROM', 'ROS', 'RPJ', 'RPM', 'RPS']

    df['train_type'] = df['Numer pociągu'].map(train_type_mapping)
    df['traction_type'] = np.where(df['Numer pociągu'].isin(traction_type_electric), 'electric', 'combustion') 

    df.drop(['Data', 'Przyjazd planowy', 'Odjazd planowy', 'Numer pociągu'], axis=1, inplace=True)
    return df

def count_distances(main_df, gps_df, big_city_names_filepath):
    pks = main_df['pk'].unique()
    dfs_list = []

    big_city_names = pd.read_csv(big_city_names_filepath, sep=';')['miasto'].unique()
    big_city_stations_gps = gps_df[gps_df['Stacja'].isin(big_city_names)].reset_index(drop=True).copy()

    for pk in pks:
        temp_df = main_df[main_df['pk'] == pk].reset_index(drop=True).copy()
        distance_to_prev_station_list = []
        for i in range(len(temp_df)):
            curr_gps = (temp_df.loc[i, 'lat'].item(), temp_df.loc[i, 'lon'].item())
            dist_to_near_city_list = []

            for j in range(len(big_city_stations_gps)):
                curr_city_gps = (big_city_stations_gps.loc[j, 'lat'], big_city_stations_gps.loc[j, 'lon'])
                dist_to_near_city = haversine(curr_gps, curr_city_gps)
                dist_to_near_city_list.append(dist_to_near_city)

            pos = np.array(dist_to_near_city_list).argmin()
            temp_df.loc[i, 'distance_to_near_city_station'] = dist_to_near_city_list[pos]
            temp_df.loc[i, 'near_city_station_name'] = big_city_stations_gps.loc[pos, 'Stacja']

            if i == 0:
                distance_to_prev_station_list.append(0)
            else:
                prev_gps = (temp_df.loc[i - 1, 'lat'].item(), temp_df.loc[i - 1, 'lon'].item())
                distance = haversine(curr_gps, prev_gps, unit=Unit.KILOMETERS)
                distance_to_prev_station_list.append(distance)

        temp_df['distance_to_prev_station'] = distance_to_prev_station_list
        temp_df['distance_from_start'] = temp_df['distance_to_prev_station'].cumsum()
        temp_df['distance_to_final'] = np.array(temp_df['distance_from_start'][::-1])
        temp_df['full_route_distance'] = temp_df.groupby('pk')['distance_to_prev_station'].transform('sum')
        dfs_list.append(temp_df)

    new_data = pd.concat(dfs_list, ignore_index=True)
    return new_data

def count_distances_new(main_df, railroads):
    pks = main_df['pk'].unique()
    dfs_list = []
    buffer_dist = 0.05

    for pk in pks:
        temp_df = main_df[main_df['pk'] == pk].reset_index(drop=True).copy()
        fitted_routes = []
        route_dist_km = []
        for i in range(1, len(temp_df)):
            prev_station = temp_df.loc[i-1, 'geometry_station'].buffer(buffer_dist)
            curr_station = temp_df.loc[i, 'geometry_station'].buffer(buffer_dist)

            for route in railroads:
                if route.intersects(prev_station) and route.intersects(curr_station):
                    difference_line = route.difference(prev_station.union(curr_station))
                    fitted_routes.append(difference_line)

            route_gdf = gpd.GeoDataFrame(geometry=diff_lines)
            route_gdf.crs = "EPSG:4326"
            route_gdf_projected = route_gdf.to_crs("EPSG:32610")
            total_distance_km = route_gdf_projected.geometry.length.sum() / 1000
            route_dist_km.append(total_distance_km)

            

            




def fix_dates(df, col_name):
    pks = df['pk'].unique()
    dfs_list = []
    np_day = np.timedelta64(1, 'D')
    for pk in pks:
        df_temp = df[df['pk'] == pk]
        dates = df_temp[col_name].values
        date_change_flg = False

        for i in range(1, len(dates)):
            prev_date = dates[i - 1]
            curr_date = dates[i]

            if (curr_date - prev_date) / np_day < 0:
                date_change_flg = True
                change_on = i
                break

        if date_change_flg:
            new_dates = dates.copy()
            new_dates[change_on:] += pd.Timedelta(days=1)
            df_temp[col_name] = new_dates

        dfs_list.append(df_temp)
    new_data = pd.concat(dfs_list, ignore_index=True)
    return new_data

def apply_date_features(data):
    # weekdays - OHE
    # data['weekday'] = data['arrival_on_time'].dt.strftime('%A')
    # weekday_dummies = pd.get_dummies(data['weekday'], prefix='weekday', dtype=float)
    # data = pd.concat([data.drop('weekday', axis=1), weekday_dummies], axis=1)

    # Applying trigonometric transformations
    data['month'] = data['arrival_on_time'].dt.month
    data['weekofyear'] = data['arrival_on_time'].dt.isocalendar().week
    data['yearday'] = data['arrival_on_time'].dt.dayofyear
    data['monthday'] = data['arrival_on_time'].dt.day
    data['weekday'] = data['arrival_on_time'].dt.dayofweek
    data['hour'] = data['arrival_on_time'].dt.hour
    data['minute'] = data['arrival_on_time'].dt.minute
    data['second'] = data['arrival_on_time'].dt.second

    data['month_sin'] = np.sin(2 * np.pi * data['month'] / 12)
    data['month_cos'] = np.cos(2 * np.pi * data['month'] / 12)

    data['weekofyear_sin'] = np.sin(2 * np.pi * data['weekofyear'] / 52)
    data['weekofyear_cos'] = np.cos(2 * np.pi * data['weekofyear'] / 52)

    data['yearday_sin'] = np.sin(2 * np.pi * data['yearday'] / 365)
    data['yearday_cos'] = np.cos(2 * np.pi * data['yearday'] / 365)

    data['monthday_sin'] = np.sin(2 * np.pi * data['monthday'] / 31)
    data['monthday_cos'] = np.cos(2 * np.pi * data['monthday'] / 31)

    data['weekday_sin'] = np.sin(2 * np.pi * data['weekday'] / 7)
    data['weekday_cos'] = np.cos(2 * np.pi * data['weekday'] / 7)

    data['hour_sin'] = np.sin(2 * np.pi * data['hour'] / 24)
    data['hour_cos'] = np.cos(2 * np.pi * data['hour'] / 24)

    data['minute_sin'] = np.sin(2 * np.pi * data['minute'] / 60)
    data['minute_cos'] = np.cos(2 * np.pi * data['minute'] / 60)

    data['second_sin'] = np.sin(2 * np.pi * data['second'] / 60)
    data['second_cos'] = np.cos(2 * np.pi * data['second'] / 60)

    data.drop(['month', 'weekofyear', 'yearday', 'monthday', 'weekday', 'hour', 'minute', 'second'], axis=1, inplace=True)

    # bank holidays ---
    def days_until_bank_holiday(row, month, day, datetime_col_name):
        current_year = row[datetime_col_name].year
        bank_holiday_date = pd.to_datetime(f'{current_year}-{month}-{day}')
        return (bank_holiday_date - row[datetime_col_name]).days
    
    data['days_until_christmas'] = data.apply(lambda row: days_until_bank_holiday(row, 12, 25, 'arrival_on_time'), axis=1)
    data['days_until_november_1_st'] = data.apply(lambda row: days_until_bank_holiday(row, 11, 1, 'arrival_on_time'), axis=1)
    data['days_until_new_year_eve'] = data.apply(lambda row: days_until_bank_holiday(row, 12, 31, 'arrival_on_time'), axis=1)
    data['days_until_easter'] = data.apply(lambda row: days_until_bank_holiday(row, 4, 5, 'arrival_on_time'), axis=1)

    return data

def get_specific_routes(df, limit):
    grouped = df.groupby('pk')['Stacja'].agg(list).reset_index()
    grouped['sorted_stations'] = grouped['Stacja'].apply(lambda x: sorted(x))

    df = pd.merge(df, grouped[['pk', 'sorted_stations']], how='left', on='pk')
    df['sorted_stations'] = df['sorted_stations'].apply(lambda x: '_'.join(x))

    storted_stations_count = df.groupby('sorted_stations')['pk'].size().to_frame().reset_index()
    stations_to_select = storted_stations_count[storted_stations_count['pk']>=limit]['sorted_stations'].tolist()

    df = df[df['sorted_stations'].isin(stations_to_select)].reset_index(drop=True)
    df.drop('sorted_stations', axis=1, inplace=True)
    return df

def get_route_names(df):
    grouped = df.groupby('pk')['Stacja'].agg(list).reset_index()
    grouped['sorted_stations'] = grouped['Stacja'].apply(lambda x: sorted(x))

    df = pd.merge(df, grouped[['pk', 'sorted_stations']], how='left', on='pk')
    df['sorted_stations'] = df['sorted_stations'].apply(lambda x: '_'.join(x))
    return df

def fix_polish_chars(pattern):
    polish_characters = {
    'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
    'ó': 'o', 'ś': 's', 'ż': 'z', 'ź': 'z',
    'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
    'Ó': 'O', 'Ś': 'S', 'Ż': 'Z', 'Ź': 'Z'
    }

    string_with_replaced_chars = "".join(polish_characters.get(char, char) for char in pattern)
    return string_with_replaced_chars

def join_spatial_data(df, voivodeships, counties, boroughs):
    df['geometry'] = [Point(xy) for xy in zip(df['lon'], df['lat'])]
    df = gpd.GeoDataFrame(df, crs="EPSG:4326")

    joined_voivodeships = gpd.sjoin(df, voivodeships[['geometry', 'JPT_NAZWA_']], how="left", op="within").drop('index_right', axis=1)
    joined_voivodeships_counties = gpd.sjoin(joined_voivodeships, counties[['geometry', 'JPT_NAZWA_']], how="left", op="within").drop('index_right', axis=1)
    joined_voivodeships_counties_boroughs = gpd.sjoin(joined_voivodeships_counties, boroughs[['geometry', 'JPT_NAZWA_']], how="left", op="within").drop('index_right', axis=1)

    joined_voivodeships_counties_boroughs.rename(columns={
        'JPT_NAZWA__left': 'voivodeship',
        'JPT_NAZWA__right': 'county',
        'JPT_NAZWA_': 'borough',
        'geometry': 'geometry_station'
    }, inplace=True)

    joined_voivodeships_counties_boroughs['voivodeship'] = joined_voivodeships_counties_boroughs['voivodeship'].fillna('zagranica')
    
    return joined_voivodeships_counties_boroughs

def geometry_point_to_lat_lon(df):
    df['lat'] = df['geometry'].apply(lambda row: row.y)
    df['lon'] = df['geometry'].apply(lambda row: row.x)
    df.drop('geometry', axis=1, inplace=True)
    return df

def convert_to_geometry(coords):
    if len(coords) == 1:
        return Point(coords[0])
    else:
        return LineString(coords)
    
def create_small_polygon(point, distance):
    return point.buffer(distance)
    
    



