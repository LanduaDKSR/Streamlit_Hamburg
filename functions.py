import numpy as np
import pandas as pd
import math
from geojson import LineString as geoLS


def trip_layer(data):
    geo_list = pd.DataFrame(np.zeros((len(data)),dtype=object),columns=['geo_json'])                          
    for i in range(0,len(data)):                       
        z_list = [0] * len(data['timestamps_list'][i])
        list0 = data['coordinates'][i]
        list1 = np.insert(list0,2,z_list,axis=1)
        list2 = np.insert(list1,3,data['timestamps_list'][i],axis=1)       
        geo_list.iloc[i] = [geoLS(list2.tolist())]
    return geo_list


def geo_distance(point1, point2):
    R = 6378.137 # Radius of earth in KM
    dLat = point2[1] * math.pi / 180 - point1[1] * math.pi / 180
    dLon = point2[0] * math.pi / 180 - point1[0] * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(point1[1] * math.pi / 180) * math.cos(point2[1] * math.pi / 180) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return d * 1000 # meters


#Liegen Start- und/oder Zielpunkt eines Trips in der Nähe eines POI
def point_of_interest(list=[],point=[],radius=200):
    d_0 = geo_distance(list[0],point)
    d_1 = geo_distance(list[-1],point)
    if d_0 <= radius:
        if d_1 <= radius:
            return 'Hin und zurück'
        else:
            return 'Vom Hbf weg'
    elif d_1 <= radius:
        return 'Zum Hbf'
    else:
        return 'Weder/noch'