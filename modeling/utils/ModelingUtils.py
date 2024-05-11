import numpy as np

def make_ml_target_classification(df):
    df['ML_TARGET'] = np.select(
        [
            df['Opóźnienie przyjazdu'] <= 5,
            (df['Opóźnienie przyjazdu'] > 5) & (df['Opóźnienie przyjazdu'] <= 20),
            (df['Opóźnienie przyjazdu'] > 20) & (df['Opóźnienie przyjazdu'] <= 60),
            df['Opóźnienie przyjazdu'] > 60
        ],
        [
            0,
            1,
            2,
            3
        ]
    )

    return df

def make_ml_target_regression(df):
    df['ML_TARGET'] = np.where(df['Opóźnienie przyjazdu']<0,0,df['Opóźnienie przyjazdu'])
    return df

MODEL_FEATURES = [
    # y ---
    'ML_TARGET',

    # X ---
    'train_type',
    'traction_type',
    'station_count_on_curr_station',
    'distances',
    'durations',
    'level_crossing_count',
    'switches_count',
    'cumsum_distances',
    'distance_to_finish',
    'nearest_big_city_distance',

    # weather
    'temp',
    'feelslike',
    'humidity',
    'dew',
    'precip',
    'precipprob',
    'snow',
    'snowdepth',
    'preciptype',
    'windgust',
    'windspeed',
    'winddir',
    'pressure',
    'visibility',
    'cloudcover',
    'solarradiation',
    'solarenergy',
    'uvindex',
    'conditions',
    'icon',

    # break duration
    'stop_duration',
    'stop_duration_lag1',
    'stop_duration_lag2',
    'stop_duration_lag3',
    'stop_duration_lag4',
    'stop_duration_lag5',
    'stop_duration_lag6',

    # time
    'month_sin',
    'month_cos',
    'weekofyear_sin',
    'weekofyear_cos',
    'weekofyear_cos',
    'yearday_sin',
    'yearday_cos',
    'monthday_sin',
    'monthday_cos',
    'weekday_sin',
    'weekday_cos',
    'hour_sin',
    'hour_cos',
    'minute_sin',
    'minute_cos',
    'second_sin',
    'second_cos',
    'days_until_christmas',
    'days_until_november_1_st',
    'days_until_new_year_eve',
    'days_until_easter',

    # spatial info and railway infra data
    'in_poland',
    'railway_distance_gmina',
    'stations_odometer_gmina',
    'level_crossing_odometer_gmina',
    'switches_odometer_gmina',
    'railway_distance_powiat',
    'stations_odometer_powiat',
    'level_crossing_odometer_powiat',
    'switches_odometer_powiat',

    # gus data
    'powierzchnia_km2_gmina',
    'ludnosc_gmina',
    'gestosc_zaludnienia_1km2_gmina',
    'powierzchnia_km2_powiat',
    'ludnosc_powiat',
    'gestosc_zaludnienia_1km2_powiat',

]
