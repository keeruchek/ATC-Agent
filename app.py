import requests
import numpy as np
import time
import os
import json
import warnings
from urllib3.exceptions import NotOpenSSLWarning

# Clean up terminal warnings
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# --- 1. GLOBAL AIRPORT DATABASE ---
# The AI Agent uses these coordinates to set the radar focus
AIRPORTS = {
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "New York JFK"},
    "LHR": {"lat": 51.4700, "lon": -0.4543, "name": "London Heathrow"},
    "SIN": {"lat": 1.3644, "lon": 103.9915, "name": "Singapore Changi"},
    "LAX": {"lat": 33.9416, "lon": -118.4085, "name": "Los Angeles Intl"},
    "HND": {"lat": 35.5494, "lon": 139.7798, "name": "Tokyo Haneda"}
}

# CONFIGURATION
ACTIVE_PORT = "JFK"  # Change this to any key in AIRPORTS
SCAN_RANGE = 1.0     # Degrees (~111km)
MIN_LAT, MAX_LAT = AIRPORTS[ACTIVE_PORT]['lat'] - SCAN_RANGE, AIRPORTS[ACTIVE_PORT]['lat'] + SCAN_RANGE
MIN_LON, MAX_LON = AIRPORTS[ACTIVE_PORT]['lon'] - SCAN_RANGE, AIRPORTS[ACTIVE_PORT]['lon'] + SCAN_RANGE

def get_live_flights():
    """Fetches and cleans data from OpenSky API"""
    url = "https://opensky-network.org/api/states/all"
    params = {'lamin': MIN_LAT, 'lomin': MIN_LON, 'lamax': MAX_LAT, 'lomax': MAX_LON}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get('states', [])
    except Exception as e:
        print(f"Connection Error: {e}")
        return []

def calculate_3d_dist(p1, p2):
    """Calculates horizontal distance in km and vertical in meters"""
    # Horizontal (Haversine)
    lon1, lat1 = np.radians(p1['lon']), np.radians(p1['lat'])
    lon2, lat2 = np.radians(p2['lon']), np.radians(p2['lat'])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    h_dist = 6371 * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))
    
    # Vertical
    v_dist = abs(p1['alt'] - p2['alt'])
    return h_dist, v_dist

def issue_ai_command(callsign, instruction, priority="Normal"):
    """Voice synthesis for the AI Agent"""
    prefix = "Immediate" if priority == "High" else ""
    msg = f"{prefix} Instruction for {callsign}: {instruction}"
    print(f"🎙️ AI AGENT: {msg}")
    os.system(f'say -v Samantha "{msg}" &')

def process_airspace():
    states = get_live_flights()
    processed_flights = []
    
    # 1. Parse raw data into clean dictionaries
    for s in states:
        # Index map: 0:icao, 1:callsign, 5:lon, 6:lat, 7:alt, 9:vel, 11:vert_rate, 14:squawk
        if all(v is not None for v in [s[0], s[5], s[6], s[7], s[9]]):
            processed_flights.append({
                "id": s[1].strip() if s[1] else s[0],
                "lon": float(s[5]),
                "lat": float(s[6]),
                "alt": float(s[7]),
                "vel": float(s[9]),
                "vr": float(s[11]) if s[11] else 0,
                "squawk": s[14],
                "status": "EN_ROUTE",
                "color": "cyan"
            })

    # 2. Analyze Phase and Risks (AI Reasoning)
    n = len(processed_flights)
    for i in range(n):
        p = processed_flights[i]
        
        # CATEGORY LOGIC
        if p['squawk'] in ['7700', '7600', '7500']:
            p['status'], p['color'] = "EMERGENCY", "purple"
            issue_ai_command(p['id'], "declare emergency, priority landing cleared", "High")
        elif p['alt'] < 500:
            if p['vr'] < -0.5: p['status'], p['color'] = "LANDING", "green"
            elif p['vr'] > 0.5: p['status'], p['color'] = "TAKEOFF", "white"
        elif p['alt'] < 3000 and p['vr'] < -1.0:
            p['status'], p['color'] = "READY_TO_LAND", "blue"

        # PROXIMITY CHECK (Conflict Detection)
        for j in range(i + 1, n):
            p2 = processed_flights[j]
            h_dist, v_dist = calculate_3d_dist(p, p2)
            
            # Loss of Separation: < 5km Horizontal AND < 300m (1000ft) Vertical
            if h_dist < 5.0 and v_dist < 300:
                p['status'] = p2['status'] = "AT_RISK"
                p['color'] = p2['color'] = "red"
                issue_ai_command(p['id'], f"Traffic conflict. Climb immediately to avoid {p2['id']}", "High")
            elif h_dist < 12.0 and v_dist < 600:
                if p['status'] != "AT_RISK": 
                    p['status'], p['color'] = "POTENTIAL_RISK", "yellow"

    return processed_flights

if __name__ == "__main__":
    print(f"📡 ATC AI AGENT ONLINE: Monitoring {AIRPORTS[ACTIVE_PORT]['name']}")
    
    while True:
        flights = process_airspace()
        
        # Save to JSON for GitHub Pages
        web_payload = {
            "airport": AIRPORTS[ACTIVE_PORT],
            "timestamp": time.time(),
            "count": len(flights),
            "flights": flights
        }
        
        with open("data.json", "w") as f:
            json.dump(web_payload, f, indent=4)
            
        print(f"--- Scan Complete: {len(flights)} aircraft tracked ---")
        time.sleep(10)
