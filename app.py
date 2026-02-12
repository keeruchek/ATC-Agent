import requests
import numpy as np
import time
import json
import os

# --- 1. GLOBAL AIRPORT DATABASE ---
AIRPORTS = {
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "New York JFK"},
    "LHR": {"lat": 51.4700, "lon": -0.4543, "name": "London Heathrow"},
    "SIN": {"lat": 1.3644, "lon": 103.9915, "name": "Singapore Changi"},
    "LAX": {"lat": 33.9416, "lon": -118.4085, "name": "Los Angeles Intl"}
}

# CONFIG: GitHub Actions can override this via Env Vars
ACTIVE_PORT = os.getenv("ACTIVE_PORT", "JFK")
ap = AIRPORTS.get(ACTIVE_PORT, AIRPORTS["JFK"])
BOUNDS = {
    'lamin': ap['lat'] - 0.7, 'lamax': ap['lat'] + 0.7,
    'lomin': ap['lon'] - 0.7, 'lomax': ap['lon'] + 0.7
}

def calculate_3d_dist(p1, p2):
    """Horizontal distance (km) and Vertical separation (m)"""
    lon1, lat1 = np.radians(p1['lon']), np.radians(p1['lat'])
    lon2, lat2 = np.radians(p2['lon']), np.radians(p2['lat'])
    # Haversine Formula
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    h_dist = 6371 * (2 * np.arctan2(np.sqrt(a), np.sqrt(1-a)))
    v_dist = abs(p1['alt'] - p2['alt'])
    return h_dist, v_dist

def get_live_data():
    url = "https://opensky-network.org/api/states/all"
    headers = {'User-Agent': 'ATC-AI-Agent-Personal-Project'}
    try:
        # Public API usage: timeout is key for stability
        r = requests.get(url, params=BOUNDS, headers=headers, timeout=20)
        if r.status_code == 200:
            return r.json().get('states', [])
        else:
            print(f"API Alert: Status {r.status_code}")
            return []
    except Exception as e:
        print(f"Request Error: {e}")
        return []

def run_agent():
    raw_states = get_live_data()
    flights = []
    
    # 1. CLEANING AND INITIAL MAPPING
    for s in raw_states:
        # s[0]=icao, s[1]=callsign, s[5]=lon, s[6]=lat, s[7]=alt, s[11]=vert_rate, s[14]=squawk
        if all(v is not None for v in [s[0], s[5], s[6], s[7]]):
            flights.append({
                "id": s[1].strip() if s[1] else s[0],
                "lon": float(s[5]), "lat": float(s[6]), "alt": float(s[7]),
                "vr": float(s[11]) if s[11] else 0,
                "squawk": s[14], "status": "EN_ROUTE", "color": "cyan", "cmd": ""
            })

    # 2. AI REASONING (Phases, Emergency, Conflicts)
    for i, f in enumerate(flights):
        # Mechanical/Emergency (Purple)
        if f['squawk'] in ['7700', '7600', '7500']:
            f['status'], f['color'] = "EMERGENCY/TECH ISSUE", "purple"
            f['cmd'] = "MAYDAY. Priority vectors to runway assigned."

        # Takeoff (White) vs Landing (Green) vs Ready (Blue)
        elif f['alt'] < 600:
            if f['vr'] > 0.5: f['status'], f['color'] = "TAKEOFF", "white"
            elif f['vr'] < -0.5: f['status'], f['color'] = "LANDING", "green"
        elif f['alt'] < 3000 and f['vr'] < -1.0:
            f['status'], f['color'] = "READY_TO_LAND", "blue"

        # Proximity Logic (Red/Yellow)
        for j in range(i + 1, len(flights)):
            f2 = flights[j]
            h, v = calculate_3d_dist(f, f2)
            if h < 6.0 and v < 350: # Loss of Separation
                f['status'] = f2['status'] = "AT RISK"
                f['color'] = f2['color'] = "red"
                f['cmd'] = f"ALERT: Traffic conflict with {f2['id']}. Adjust heading."
            elif h < 12.0 and v < 600: # Potential Risk
                if f['color'] not in ['red', 'purple']:
                    f['status'], f['color'] = "POTENTIAL RISK", "yellow"

    return {"airport": ap, "time": time.ctime(), "count": len(flights), "aircraft": flights}

if __name__ == "__main__":
    final_output = run_agent()
    with open("data.json", "w") as f:
        json.dump(final_output, f, indent=4)
    print(f"Scan complete. Found {final_output['count']} aircraft near {ap['name']}.")
