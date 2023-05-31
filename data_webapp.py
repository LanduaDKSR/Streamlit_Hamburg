import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
from geojson import LineString as geoLS
import geopandas
import requests
#import json
import datetime
import ast
import scooter_config
import stations_config

from PIL import Image

st.set_page_config(layout="wide")

image = Image.open('Logo.png')

config = scooter_config.config
config2 = stations_config.config


def trip_layer(data):
    geo_list = pd.DataFrame(np.zeros((len(data)),dtype=object),columns=['geo_json'])
    geo_no_time = pd.DataFrame(np.zeros((len(data)),dtype=object),columns=['geo_json'])
                            
    for i in range(0,len(data)):                       
        z_list = [0] * len(data['timestamps_list'][i])
        list0 = data['coordinates'][i]
        list1 = np.insert(list0,2,z_list,axis=1)
        list2 = np.insert(list1,3,data['timestamps_list'][i],axis=1)
        
        geo_list.iloc[i] = [geoLS(list2.tolist())]
        geo_no_time.iloc[i] = [geoLS(list1.tolist())]

    #map_0 = KeplerGl(height=600, data={'Scooters': geo_list}, config=trip_layer_config.config)
    return geo_list


def rental_stations():
    entity = 'https://iot.hamburg.de/v1.1/Things?'
    rows = '$skip=0&$top=5000&'
    #gefiltert nach Fahrradzählstationen
    filter = '$filter=((properties%2FownerThing+eq+%27Hamburg+Verkehrsanlagen%27))'
    filter_observation = '?$skip=0&$top=1&$orderby=resultTime+desc'

    url = entity + rows + filter
    response = requests.get(url)
    things_data = response.json()

    # get a list of datastream_link from every thing
    datastreams = []
    for thing in things_data['value']:
        thing = thing['Datastreams@iot.navigationLink'] 
        datastreams.append(thing)

    ## get a list of datastreams from every thing
    # all links with last 3 observations
    observations = []
    for stream in datastreams:
        stream = requests.get(stream)
        data = stream.json()
        value = data['value']
        link = value[0]['Observations@iot.navigationLink']+filter_observation
        observations.append(link)

    final_df = pd.DataFrame() 
    result_list = []
    resultTime_list = []
    coordinates_list = []

    for observation in observations:
        request = requests.get(observation)
        data = request.json()
        values = data['value']

        for item in values:
            # result = counts and resulttime = time
            result_list.append(item['result'])
            resultTime_list.append(item['resultTime'])

            # holding coordinates
            link = item['FeatureOfInterest@iot.navigationLink']

            # Request 'FeatureOfInterest@iot.navigationLink'
            request = requests.get(link)
            feature_of_interest = request.json()
            coordinates = feature_of_interest['feature']['geometry']['coordinates']
            coordinates_list.append(coordinates)

    df = pd.DataFrame({'result': result_list, 'resultTime': resultTime_list, 'coordinates': coordinates_list})
    df['lon'] = df['coordinates'].apply(lambda x: x[0])
    df['lat'] = df['coordinates'].apply(lambda x: x[1])
    map_2 = KeplerGl(height=650, data={'Stationen': df}, config=config2)
    return df, map_2


#@st.cache_data
def load_data(source1, source2):   
    df = pd.read_csv(source1)
    df.drop(['Unnamed: 0'], axis=1, inplace=True)
    df['coordinates'] = df['coordinates'].apply(lambda x: ast.literal_eval(x))
    df['timestamps_list'] = df['timestamps_list'].apply(lambda x: ast.literal_eval(x))
    df['geo_json'] = trip_layer(df)

    stations = pd.read_excel(source2)
    stations.dropna(axis=0, inplace=True)
    gdf = geopandas.GeoDataFrame(stations, geometry=geopandas.points_from_xy(stations['Gauss-Krueger E'],stations['Gauss-Krueger N']), crs="EPSG:31467")
    gdf = gdf.to_crs("EPSG:4326")
    stations['lon'] = gdf['geometry'].x
    stations['lat'] = gdf['geometry'].y
    stations['icon'] = pd.DataFrame(['place'] * len(stations))
    stations.reset_index(inplace=True)
    stations.drop(['index'], axis=1, inplace=True)

    #df = pd.concat([df, trip_layer(df)], axis=1)
    map_1 = KeplerGl(height=650, data = {'Scooters': df, 'stations': stations[['Name', 'lon', 'lat', 'icon']]}, config=config)
    return df, map_1


def data_filter(data,dates):
    data = data[data['date'] >= dates[0]]
    filtered = data[data['date'] <= dates[1]]
    return filtered


source1 = "Hamburg_dummy_trips.csv"
source2 = "HVV-Haltestellen.xlsx" #c:/Users/FabianLandua/Documents/Data reports/Hamburg/

df, map_1 = load_data(source1, source2)
#hvv, map2 = stations_load(source2)

st.sidebar.write("""Filtern der Daten perspektivisch möglich""")
d_1 = st.sidebar.date_input('Start', datetime.date(2023,2,1))
d_2 = st.sidebar.date_input('Ende', datetime.date(2023,2,28))


#df_filtered = data_filter(df,dates)
#config['config']['visState']['filters'][0]['value'] = [dates[0].day, dates[1].day]

header1, header2 = st.columns([3,1])
with header1:
    st.write("""
    # Urban Data Challenge Hamburg
    Mockup
    """)

with header2:
    st.image(image)


#st.dataframe(df_filtered)

tab1, tab2 = st.tabs(["Scooter und ÖPNV", "Leihstationen"])

with tab1:
    col1, col2 = st.columns([3,1])
    with col1:
        #map_1.config = config
        keplergl_static(map_1)
    with col2:
        st.write("""Für diese Visualisierung wurden virtuellen Trip-Daten erzeugt. Die Daten bilden keine realen Trips ab und dienen rein zur Veranschaulichung der Darstellbarkeit.
                Die Informationen über Positionen der HVV-Stationen wurden dem Open-Data-Portal entnommen und in das entsprechende Koordinatensystem transformiert.""")

    st.write("""
    ### Rohdaten
    """)
    st.dataframe(df)

with tab2:
    col1, col2 = st.columns([3,1])
    with col1:
        if st.button('Verfügbarkeiten berechnen'):
            rental, map_2 = rental_stations()
        else:
            rental, map_2 = [], KeplerGl(height=650, config=config2)
        #map_1.config = config
        #rental = rental_stations()
        keplergl_static(map_2)
    with col2:
        st.write("""Aktuelle Verfügbarkeit an Fahrrad-Leihstationen.
        Auf Knopfdruck lässt sich die aktuelle Situation anzeigen. (Ladezeit ca. 1 Minute)""")
        

    st.write("""
    ### Rohdaten
    """)
    st.dataframe(rental)

