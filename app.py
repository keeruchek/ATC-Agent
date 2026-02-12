import requests
import numpy as np
import time
import matplotlib.pyplot as plt
import os

# --- 1. CONFIGURATION ---
AREA = {'lamin': 40.0, 'lomin': -74.0, 'lamax': 41.0, 'lomax': -73.0}
plt.ion()
fig,ax = plt.subplots()
# 1. Define your "Watch Zone" (Bounding Box)
# Example: Coordinates for a 1-degree box around a major airport
# [min_lat, min_lon, max_lat, max_lon]


def get_live_flights():
    url = "https://opensky-network.org/api/states/all"
    response = requests.get(url, params=AREA)
    data = response.json()
    
    # OpenSky returns a list of 'states'. 
    # Index 5 = longitude, 6 = latitude, 7 = baro_altitude, 9 = velocity
    flight_list = []
    if data['states']:
        for s in data['states']:
            # We filter out None values to keep the math clean
            if all(v is not None for v in [s[5], s[6], s[7], s[9]]):
                flight_list.append([s[0], s[5], s[6], s[9]])
    
    return np.array(flight_list)
def calculate_proximity(matrix):
    n=len(matrix)
    if n<2:return None
    dist_matrix = np.zeros((n,n))
    for i in range(n):
        lon1 = np.radians(float(matrix[i][1])) 
        lat1 = np.radians(float(matrix[i][2]))
        for j in range(i+1,n):
            lon2 = np.radians(float(matrix[j][1]))
            lat2 = np.radians(float(matrix[j][2]))
            
            dlat, dlon = lat2 - lat1, lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            
            # This is the line that was failing before
            distance = 6371 * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))
            dist_matrix[i, j] = dist_matrix[j, i] = round(distance, 2)
    return dist_matrix
# 2. Run the collector
print("Fetching live airspace data...")
raw_data = get_live_flights()
print(f"Found {len(raw_data)} planes in the zone.")
print("Sample Matrix Row (Lon, Lat, Alt, Velocity):")
print(raw_data[0])
class HistoryBuffer:
    def __init__(self):
        self.history = {}
    def get_vector(self, icao, lat, lon):
        current_time = time.time()
        if icao in self.history:
            prev_lat, prev_lon, prev_time = self.history[icao]
            dt = current_time - prev_time
            d_lat = (lat - prev_lat)/dt
            d_lon = (lon - prev_lon)/dt
            self.history[icao] = [lat,lon, current_time]
            return d_lat, d_lon
        self.storage[icao] = [lat,lon,current_time]
        return 0.0, 0.0
    def update_and_get_history(self, callsign, current_lat, current_lon):
        if callsign in self.history:
            prev_lat, prev_lon = self.history[callsign]
            d_lat = current_lat - prev_lat
            d_lon = current_lon - prev_lon
            self.history[callsign] = [current_lat, current_lon]
            return d_lat, d_lon
        self.history[callsign] = [current_lat, current_lon]
        return 0,0
if __name__=="__main__":
    while True:
        print("\n---Scanning Airspace---")
        raw_data = get_live_flights()
        if raw_data is not None and len(raw_data)>0:
            print(f"Tracking {len(raw_data)}aircraft.")
            ax.clear()
            lons = raw_data[:,1].astype(float)
            lats = raw_data[:,2].astype(float)
            ax.scatter(lons, lats, c='red', marker=r'^')
            ax.set_xlim(AREA['lomin'], AREA['lomax'])
            ax.set_ylim(AREA['lamin'], AREA['lamax'])
            ax.set_title(f"Live ATC - {len(raw_data)} Aircraft")
            plt.draw()
            plt.pause(0.1)
            distance = calculate_proximity(raw_data)
            if distance is not None:
                conflicts = np.where((distance < 10) & (distance > 0))
                pairs = zip(conflicts[0], conflicts[1])
                for i, j in pairs:
                    if i < j: # Avoid reporting the same pair twice (i,j and j,i)
                        id1, id2 = raw_data[i][0], raw_data[j][0]
                        print(f"⚠️ CONFLICT: {id1} and {id2} are only {distance[i,j]}km apart!")
