import requests
import numpy as np
import time
import matplotlib.pyplot as plt
import os
import json
import warnings
from urllib3.exceptions import NotOpenSSLWarning

# Suppress the Mac LibreSSL warning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# --- 1. CONFIGURATION ---
# [min_lat, min_lon, max_lat, max_lon]
AREA = {'lamin': 40.0, 'lomin': -74.0, 'lamax': 41.0, 'lomax': -73.0}

plt.ion()
fig, ax = plt.subplots(figsize=(10, 8))

def get_live_flights():
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, params=AREA, timeout=10)
        data = response.json()
        
        flight_list = []
        if data and 'states' in data and data['states']:
            for s in data['states']:
                # Index 0=ICAO, 5=Lon, 6=Lat, 7=Alt, 9=Velocity
                if all(v is not None for v in [s[0], s[5], s[6], s[7], s[9]]):
                    flight_list.append([s[0], s[5], s[6], s[7], s[9]])
        
        return np.array(flight_list)
    except Exception as e:
        print(f"API Error: {e}")
        return None

def calculate_proximity(matrix):
    n = len(matrix)
    if n < 2: return None
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        # Index 1 is Lon, Index 2 is Lat
        lon1 = np.radians(float(matrix[i][1])) 
        lat1 = np.radians(float(matrix[i][2]))
        for j in range(i + 1, n):
            lon2 = np.radians(float(matrix[j][1]))
            lat2 = np.radians(float(matrix[j][2]))
            
            dlat, dlon = lat2 - lat1, lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            distance = 6371 * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))
            dist_matrix[i, j] = dist_matrix[j, i] = round(distance, 2)
    return dist_matrix

def issue_command(id1, id2, dist):
    msg = f"Alert. Traffic conflict between {id1} and {id2}. Distance {dist} kilometers."
    print(f"🎙️ AGENT: {msg}")
    # Mac 'say' command for the AI voice
    os.system(f'say -v Samantha "{msg}" &') 

class HistoryBuffer:
    def __init__(self):
        self.history = {} # Key: ICAO, Value: [lat, lon, timestamp]

    def update_and_get_vector(self, icao, lon, lat):
        current_time = time.time()
        if icao in self.history:
            prev_lon, prev_lat, prev_time = self.history[icao]
            dt = current_time - prev_time
            if dt > 0:
                d_lon = (float(lon) - float(prev_lon)) / dt
                d_lat = (float(lat) - float(prev_lat)) / dt
                self.history[icao] = [lon, lat, current_time]
                return d_lon, d_lat
        self.history[icao] = [lon, lat, current_time]
        return 0.0, 0.0

# Initialize AI Memory
hb = HistoryBuffer()

if __name__ == "__main__":
    print("🚀 Starting ATC AI Agent...")
    
    while True:
        raw_data = get_live_flights()
        
        if raw_data is not None and len(raw_data) > 0:
            print(f"\n--- Scanning Airspace: {len(raw_data)} Aircraft ---")
            
            # --- 1. DATA PREP ---
            lons = raw_data[:, 1].astype(float)
            lats = raw_data[:, 2].astype(float)
            ids = raw_data[:, 0]

            # --- 2. VISUALIZATION ---
            ax.clear()
            ax.set_facecolor('#0b132b') # Dark Radar Blue
            ax.grid(True, color='#1c2541', linestyle='--')
            
            # Plot planes
            ax.scatter(lons, lats, c='cyan', marker='^', s=100, edgecolors='white')
            
            # Add labels for IDs
            for i, txt in enumerate(ids):
                ax.annotate(txt, (lons[i], lats[i]), color='white', fontsize=8, xytext=(5,5), textcoords='offset points')

            ax.set_xlim(AREA['lomin'], AREA['lomax'])
            ax.set_ylim(AREA['lamin'], AREA['lamax'])
            ax.set_title(f"ATC RADAR ACTIVE - {time.strftime('%H:%M:%S')}", color='red')
            plt.draw()
            plt.pause(0.1)

            # --- 3. PROXIMITY & AGENT LOGIC ---
            distance = calculate_proximity(raw_data)
            current_conflicts = []

            if distance is not None:
                conflicts = np.where((distance < 10) & (distance > 0))
                pairs = zip(conflicts[0], conflicts[1])
                
                for i, j in pairs:
                    if i < j:
                        id1, id2 = ids[i], ids[j]
                        dist = distance[i, j]
                        print(f"⚠️ CONFLICT: {id1} | {id2} | {dist}km")
                        issue_command(id1, id2, dist)
                        current_conflicts.append({"p1": id1, "p2": id2, "dist": dist})

            # --- 4. EXPORT FOR GITHUB PAGES ---
            web_data = {
                "last_update": time.strftime('%Y-%m-%d %H:%M:%S'),
                "count": len(raw_data),
                "aircraft": raw_data.tolist(),
                "conflicts": current_conflicts
            }
            with open("data.json", "w") as f:
                json.dump(web_data, f)

        time.sleep(10)
