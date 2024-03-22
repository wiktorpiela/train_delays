import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from typing import List
import requests
import os
from dotenv import load_dotenv
load_dotenv()

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
            lat_list.append(-1.0)
            long_list.append(-1.0)

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
            lat = -1.0
            lng = -1.0

        lat_list.append(lat)
        long_list.append(lng)

    df_out = pd.DataFrame({
        'Stacja': string_location_list,
        'lat': lat_list,
        'lon': long_list}
    )
    return df_out

def get_historical_weather(location_df):
    api_key=os.environ['WEATHER_API_KEY']
    location_df['date'] = pd.to_datetime(location_df['date']).dt.date
    #location_df['formatted_datetime'] = location_df['datetime'].apply(lambda x: x.strftime('%Y-%m-%dT%H:%M:%S'))
    weather_dfs_list = []
    for i in range(len(location_df)):
        lat = location_df.loc[i, 'lat']
        lon = location_df.loc[i, 'lon']
        date = location_df.loc[i, 'date']
        url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{lat},{lon}/{date}/{date}?unitGroup=metric&key={api_key}'
        response = requests.get(url)
        data = pd.DataFrame(response.json()['days'][0]['hours'])
        data.insert(0,'date', date)
        data.insert(0, 'lon', lon)
        data.insert(0, 'lat', lat)
        weather_dfs_list.append(data)
        print(i/len(location_df)*100)

    location_df = pd.concat(weather_dfs_list, ignore_index=True)

    return location_df

def get_route_attributes(latA:float, lonA:float, latB:float, lonB:float):

    req_body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": latA,
                    "longitude": lonA
                    }
                }
            },

        "destination": {
            "location": {
                "latLng": {
                    "latitude": latB,
                    "longitude": lonB
                    }
                }
            },
            
        "travelMode": "TRANSIT",
        "transitPreferences": {
            "allowedTravelModes": ["TRAIN", "RAIL"]
            }
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": os.environ['GOOGLE_MAPS_API_KEY'],
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
    }

    response = requests.post("https://routes.googleapis.com/directions/v2:computeRoutes", json=req_body, headers=headers)

    if response.status_code == 200:
        data = response.json()

        if "error" in data:
            print(data["error"])
            distance, duration, encoded_polyline = np.nan, np.nan, np.nan

        elif "routes" in data:
            distance = data['routes'][0]['distanceMeters']
            duration = float(data['routes'][0]['duration'].replace('s',''))
            encoded_polyline = data['routes'][0]['polyline']['encodedPolyline']

        else:
            print("No routes found. Something might be wrong with request data")
            distance, duration, encoded_polyline = np.nan, np.nan, np.nan
            
    else:
        print("Error:", response.status_code)
        distance, duration, encoded_polyline = np.nan, np.nan, np.nan

    return (distance, duration, encoded_polyline)

