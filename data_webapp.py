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
import folium
import altair as alt
from streamlit_folium import st_folium

from functions import trip_layer, point_of_interest
from PIL import Image

st.set_page_config(layout="wide")

image = Image.open('Logo.png')
image_FHH = Image.open('Logo_FHH.gif')

config = scooter_config.config
config_2 = stations_config.config


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
    
    return df#, map_2


@st.cache_data
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
    
    return df, stations


def data_filter(data,dates):
    data = data[data['date'] >= dates[0]]
    filtered = data[data['date'] <= dates[1]]
    return filtered


source1 = "Hamburg_dummy_trips.csv"
source2 = "HVV-Haltestellen.xlsx" #c:/Users/FabianLandua/Documents/Data reports/Hamburg/

df, stations = load_data(source1, source2)
map_1 = KeplerGl(height=650, data = {'Scooters': df, 'stations': stations[['Name', 'lon', 'lat', 'icon']]}, config=config)
#hvv, map2 = stations_load(source2)

#st.sidebar.write("""Filtern der Daten perspektivisch möglich""")
d_1 = st.sidebar.date_input('Start', datetime.date(2023,2,1))
d_2 = st.sidebar.date_input('Ende', datetime.date(2023,2,28))


#df_filtered = data_filter(df,dates)
#config['config']['visState']['filters'][0]['value'] = [dates[0].day, dates[1].day]

header1, header2 = st.columns([3,0.9])
with header1:
    st.write("""
    # URBAN DATA CHALLENGE HAMBURG
    ### Mockup: 3D-Datencheck für nachhaltige Stadtmobilität
    """)

with header2:
    st.text("")
    st.text("")
    header21, header22, header32 = st.columns([1,1,0.2])
    with header22:
        st.image(image_FHH)
    header31, header32 = st.columns([1,3])
    with header32:
        st.image(image)

#with header3:
#    st.image(image)


#st.dataframe(df_filtered)

tab1, tab2, tab3 = st.tabs(["Scooter und ÖPNV", "Point of Interest (POI)", "Leihstationen"])

with tab1:
    col11, col12 = st.columns([3,1])
    with col11:
        #map_1.config = config
        keplergl_static(map_1)
    with col12:
        st.write("""
                ### Die letzte Meile
                Wie gliedern sich Scooter-Fahrten in das ÖPNV-Netz ein?
                Für diese Visualisierung wurden **virtuelle Trip-Daten** erzeugt. Die Daten bilden keine realen Trips ab und dienen allein zur Veranschaulichung der Darstellbarkeit.
                Die Informationen über Positionen der HVV-Stationen wurden dem Open-Data-Portal entnommen und in das entsprechende Koordinatensystem transformiert.""")
        st.markdown("""---""")
        st.text("")
        st.text("")
        st.text("")
        #st.text("")
        #st.text("")
        #st.text("")

        fig = plt.figure(figsize=(6, 4))
        fig.patch.set_facecolor("#F5F7FA")
        sns.set_style(rc = {'axes.facecolor': "#F5F7FA"})
        sns.histplot(x='length_km', data=df, bins=50, kde=True)
        st.pyplot(fig)

    st.write("""
    ### Rohdaten
    """)
    st.dataframe(df)

# POI Analyse
Hbf = [10.008, 53.5527]
colors = ["#FFED00", "#C00000", "#164194", "#3E7A48"]

with tab2:
    col21, col22, col23 = st.columns([1.2,1.8,1])
    with col21:
        radius = st.slider('Radius', 0, 1000, 500, 50)
        df['Hbf'] = df['coordinates'].apply(lambda x: point_of_interest(x,point=Hbf,radius=radius))
        map_point = pd.DataFrame({'Name': ['Hauptbahnhof'], 'lon': [Hbf[0]], 'lat': [Hbf[1]], 'Radius': radius})

        map = folium.Map(location=[Hbf[1], Hbf[0]], zoom_start=14)
        folium.Circle([Hbf[1], Hbf[0]],
                            radius=radius,
                            tooltip="Umkreis",
                            fill=True,
                            color="purple").add_to(map)
        folium.Marker([Hbf[1], Hbf[0]],
                    tooltip="Hamburg Hbf").add_to(map)

        st_data = st_folium(map, height=300, width=300)

    with col22:
        # Gesamtübersicht
        base = alt.Chart(df).encode(
                    x=('count(Hbf):Q'),
                    y='Hbf',
                    color=alt.Color('Hbf:N', scale=alt.Scale(range=colors)),
                    tooltip=[alt.Tooltip('count():Q', title='Anzahl Fahrten')]
                ).properties(height=200)
        fig = base.mark_bar() + base.mark_text(align='left',dx=2)
        st.altair_chart(fig, theme="streamlit", use_container_width=True)

        # Nach Fahrstrecke
        fig_2 = alt.Chart(df).mark_bar(size=14, opacity=0.8, ).encode(
                alt.X("length_km", bin=alt.Bin(extent=[0, 16], step=0.5)),
                y='count(length_km)',
                color=alt.Color('Hbf:N', scale=alt.Scale(range=colors), legend=None),
                order=alt.Order('Hbf'),
                tooltip=[alt.Tooltip('length_km:Q', title='Fahrstrecke'), alt.Tooltip('count():Q', title='Anzahl Fahrten')]
                ).properties(height=250)
        st.altair_chart(fig_2, theme="streamlit", use_container_width=True)

    with col23:
        st.write("""
                ### Punktuelle Analysen
                Die betrachteten Daten lassen sich nach unterschiedlichen Attributen filtern, bewerten oder neu sortieren. Hierbei können spielerische Elemente und die Interaktion der Nutzenden zu mehr Interesse an den Inhalten führen.
                Gleichzeitig soll an diesem Beispiel gezeigt werden, wie ohne die Darstellung einzelner Fahrten eine Interpretation der Daten übermittelt werden kann.""")
        st.markdown("""---""")


with tab3:
    col31, col32 = st.columns([3,1])
    with col31:
        if st.button('Verfügbarkeiten berechnen'):
            rental = rental_stations()
            map_2 = KeplerGl(height=650, data={'Stationen': rental}, config=config_2)
        else:
            rental, map_2 = [], KeplerGl(height=650, config=config)
        #map_1.config = config
        #rental = rental_stations()
        keplergl_static(map_2)
    with col32:
        st.text("")
        st.text("")
        st.text("")
        st.write("""Aktuelle Verfügbarkeit an Fahrrad-Leihstationen.
        Auf Knopfdruck lässt sich die aktuelle Situation anzeigen.""")
        st.write("""Dies kann je nach Internetverbindung einige Minuten dauern.""")
        

    st.write("""
    ### Rohdaten
    """)
    st.dataframe(rental)

