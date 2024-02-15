import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from typing import List
import requests
import os
load_dotenv()

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

def osm_geocoder(string_location_list:List[str]):
    nom = Nominatim(user_agent=os.environ['MY_AGENT'])
    lat_list = []
    long_list = []

    for i in range(len(string_location_list)):
        lookup_place = f'{string_location_list}, Railway Station'
        res = nom.geocode(lookup_place)

        if res is not None:
            lat_list.append(res.latitude)
            long_list.append(res.longitude)
        else:
            lat_list.append(0.0)
            long_list.append(0.0)

    df_out = pd.DataFrame({
        'Stacja':string_location_list,
        'lat': lat_list,
        'lon': long_list}
    )
    return df_out

def google_maps_geocoder(string_location_list:List[str]):
    api_key = os.environ['GOOGLE_MAPS_API_KEY']
    url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    lat_list = []
    long_list = []

    for i in range(len(string_location_list)):

        lookup_place = f'{string_location_list[i]}, Railway Station'
        params = {'key': api_key, 'address': lookup_place}
        response = requests.get(url, params=params).json()

        try:
            lat = response['results'][0]['geometry']['location']['lat']
            lng = response['results'][0]['geometry']['location']['lng']
        except IndexError:
            lat = 0
            lng = 0

        lat_list.append(lat)
        long_list.append(lng)

    df_out = pd.DataFrame({
        'Stacja': string_location_list,
        'lat': lat_list,
        'lon': long_list}
    )
    return df_out