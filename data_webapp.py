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
import json
import datetime
import ast
#import map_config

st.set_page_config(layout="wide")
#config = map_config.config

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
    stations.reset_index(inplace=True)
    stations.drop(['index'], axis=1, inplace=True)

    #df = pd.concat([df, trip_layer(df)], axis=1)
    map_1 = KeplerGl(height=500, data = {'Scooters': df, 'stations': stations[['Name', 'lon', 'lat']]})
    return df, map_1


def data_filter(data,dates):
    data = data[data['date'] >= dates[0]]
    filtered = data[data['date'] <= dates[1]]
    return filtered


source1 = "c:/Users/FabianLandua/Documents/Data reports/Hamburg/Hamburg_dummy_trips.csv"
source2 = "c:/Users/FabianLandua/Documents/Data reports/Hamburg/HVV-Haltestellen.xlsx"

df, map_1 = load_data(source1, source2)
#hvv, map2 = stations_load(source2)

d_1 = st.sidebar.date_input('Start', datetime.date(2023,2,1))
d_2 = st.sidebar.date_input('Ende', datetime.date(2023,2,28))


#df_filtered = data_filter(df,dates)
#config['config']['visState']['filters'][0]['value'] = [dates[0].day, dates[1].day]


st.write("""
# My first app
Hello *world!*
LOGO
""")


col1, col2 = st.columns([2,1])
with col1:

    #map_1.config = config
    keplergl_static(map_1)

    st.write("""
    ## Rohdaten
    """)
    #st.dataframe(df_filtered)

with col2:
    tab1, tab2 = st.tabs(["Fahrstrecke", "Fahrtzeit"])
"""
    with tab1:
        fig = plt.figure(figsize=(10, 6))
        sns.histplot(x='trip_distance', data=df_filtered, bins=50, kde=True)
        st.pyplot(fig)

    with tab2:
        fig2 = plt.figure(figsize=(10, 6))
        sns.histplot(x='trip_duration', data=df_filtered, bins=50, kde=True)
        st.pyplot(fig2)
"""
