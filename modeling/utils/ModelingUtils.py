import numpy as np
import pandas as pd
def make_ml_target(df):
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

MODEL_FEATURES = [
    'station_count_on_curr_station', 
    'full_route_station_count',
    'distance_to_near_city_station', 
    'near_city_station_name',
    'distance_to_prev_station', 
    'distance_from_start', 
    'distance_to_final',
    'full_route_distance', 
    'days_until_christmas', 
    'weekday_Friday',
    'weekday_Monday', 
    'weekday_Saturday', 
    'weekday_Sunday',
    'weekday_Thursday', 
    'weekday_Tuesday', 
    'weekday_Wednesday',
    'hour_angle_sin', 
    'weekday_angle_sin', 
    'monthday_angle_sin',
    'yearday_angle_sin', 
    'weekyear_angle_sin', 
    'month_angle_sin',
    'stop_duration', 
    'stop_duration_lag1', 
    'stop_duration_lag2',
    'stop_duration_lag3', 
    'stop_duration_lag4', 
    'stop_duration_lag5',
    'stop_duration_lag6', 
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
]
