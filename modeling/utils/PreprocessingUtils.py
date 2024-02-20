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
    # days until christmas (bank holiday)
    christmas_date = pd.to_datetime('2022-12-25')
    data['days_until_christmas'] = (christmas_date - data['arrival_on_time']).dt.days

    # weekdays - OHE
    data['weekday'] = data['arrival_on_time'].dt.strftime('%A')
    weekday_dummies = pd.get_dummies(data['weekday'], prefix='weekday', dtype=float)
    data = pd.concat([data.drop('weekday', axis=1), weekday_dummies], axis=1)

    # trigonometric
    data['hour_angle_sin'] = np.sin(data['arrival_on_time'].dt.hour / 24 * 2 * np.pi)
    data['weekday_angle_sin'] = np.sin(data['arrival_on_time'].dt.dayofweek / 7 * 2 * np.pi)
    data['monthday_angle_sin'] = np.sin(data['arrival_on_time'].dt.day / 30 * 2 * np.pi)
    data['yearday_angle_sin'] = np.sin(data['arrival_on_time'].dt.dayofyear / 365 * 2 * np.pi)
    data['weekyear_angle_sin'] = np.sin(data['arrival_on_time'].dt.isocalendar().week / 52 * 2 * np.pi)
    data['month_angle_sin'] = np.sin(data['arrival_on_time'].dt.month / 12 * 2 * np.pi)

    return data