import pandas as pd
import numpy as np

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
    pass
    big_city_names = pd.read_csv('../data/big_cities_dict.csv', sep=';')['miasto'].unique()
    big_city_stations_gps = gps[gps['Stacja'].isin(big_city_names)].reset_index(drop=True).copy()

    for pk in pks:
        temp_df = data[data['pk'] == pk].reset_index(drop=True).copy()
        distance_to_prev_station_list = []
        for i in range(len(temp_df)):
            curr_gps = (temp_df.loc[i, 'lat'].item(), temp_df.loc[i, 'lon'].item())

            if i == 0:
                distance_to_prev_station_list.append(0)
            else:
                prev_gps = (temp_df.loc[i - 1, 'lat'].item(), temp_df.loc[i - 1, 'lon'].item())
                distance = haversine(curr_gps, prev_gps, unit=Unit.KILOMETERS)
                distance_to_prev_station_list.append(distance)

        temp_df['distance_to_prev_station'] = distance_to_prev_station_list
        temp_df['full_route_distance'] = temp_df.groupby('pk')['distance_to_prev_station'].transform('sum')

        dfs_list.append(temp_df)
        print(pk)

    new_data = pd.concat(dfs_list, ignore_index=True)