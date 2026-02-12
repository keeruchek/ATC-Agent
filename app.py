import requests
import numpy as np
import time
import json
import os

# --- 1. GLOBAL AIRPORT DATABASE ---
AIRPORTS = {
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "New York JFK"},
    "LHR": {"lat": 51.4700, "lon": -0.4543, "name": "London Heathrow"},
    "SIN": {"lat": 1.3644, "lon": 103.9915, "name": "Singapore Changi"}
}

# Configured via GitHub environment variables or manual edit
ACTIVE_PORT = os.getenv("ACTIVE_PORT", "JFK")
ap = AIRPORTS[ACTIVE_PORT]
BOUNDS = {
    'lamin': ap['lat']-1, 'lamax': ap['lat']+1,
    'lomin': ap['lon']-1, 'lomax': ap['lon']+1
}

def calculate_3d_dist(p1, p2):
    lon1, lat1 = np.radians(p1['lon']), np.radians(p1['lat'])
    lon2, lat2 = np.radians(p2['lon']), np.radians(p2['lat'])
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    h_dist = 6371 * (2 * np.arctan2(np.sqrt(a), np.sqrt(1-a)))
    v_dist = abs(p1['alt'] - p2['alt'])
    return h_dist, v_dist

def run_ai_agent():
    try:
        r = requests.get("https://opensky-network.org/api/states/all", params=BOUNDS, timeout=15)
        raw_states = r.json().get('states', [])
    except: return {}

    flights = []
    for s in raw_states:
        if all(v is not None for v in [s[0], s[5], s[6], s[7], s[9]]):
            flights.append({
                "id": s[1].strip() if s[1] else s[0],
                "lon": float(s[5]), "lat": float(s[6]), "alt": float(s[7]),
                "vel": float(s[9]), "vr": float(s[11]) if s[11] else 0,
                "squawk": s[14], "status": "EN_ROUTE", "color": "cyan", "command": ""
            })

    # AI Reasoning Logic
    for i, f in enumerate(flights):
        # Emergency (Purple)
        if f['squawk'] in ['7700', '7600']:
            f['status'], f['color'], f['command'] = "EMERGENCY", "purple", "Priority landing cleared."
        # Takeoff/Landing (White/Green/Blue)
        elif f['alt'] < 500:
            if f['vr'] < -0.5: f['status'], f['color'] = "LANDING", "green"
            elif f['vr'] > 0.5: f['status'], f['color'] = "TAKEOFF", "white"
        elif f['alt'] < 3000 and f['vr'] < -1.0:
            f['status'], f['color'] = "READY_TO_LAND", "blue"

        # Conflict Detection (Red/Yellow)
        for j in range(i + 1, len(flights)):
            f2 = flights[j]
            h, v = calculate_3d_dist(f, f2)
            if h < 5 and v < 300:
                f['status'] = f2['status'] = "AT_RISK"
                f['color'] = f2['color'] = "red"
                f['command'] = f"Traffic Alert. Adjust heading to avoid {f2['id']}."
            elif h < 12 and v < 600 and f['color'] not in ['red', 'purple']:
                f['status'], f['color'] = "POTENTIAL_RISK", "yellow"

    return {"airport": ap, "timestamp": time.time(), "flights": flights}

if __name__ == "__main__":
    data = run_ai_agent()
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
