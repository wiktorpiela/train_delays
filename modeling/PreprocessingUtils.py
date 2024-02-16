import pandas as pd
import numpy as np
from haversine import haversine, Unit

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

    df.drop(['Data', 'Przyjazd planowy', 'Odjazd planowy', 'Numer pociągu'], axis=1, inplace=True)
    return df

def count_distances(main_df, gps_df):
    pks = main_df['pk'].unique()
    dfs_list = []

    big_city_names = pd.read_csv('../data/big_cities_dict.csv', sep=';')['miasto'].unique()
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