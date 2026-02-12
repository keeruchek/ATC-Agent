import requests
import numpy as np
import time
import json
import os

# --- 1. GLOBAL AIRPORT DATABASE ---
# The AI uses this to center the radar and set boundaries
AIRPORTS = {
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "New York JFK"},
    "LHR": {"lat": 51.4700, "lon": -0.4543, "name": "London Heathrow"},
    "SIN": {"lat": 1.3644, "lon": 103.9915, "name": "Singapore Changi"},
    "LAX": {"lat": 33.9416, "lon": -118.4085, "name": "Los Angeles Intl"},
    "DXB": {"lat": 25.2532, "lon": 55.3657, "name": "Dubai Intl"},
    "SYD": {"lat": -33.9399, "lon": 151.1753, "name": "Sydney Kingsford Smith"}
}

# --- 2. CONFIGURATION ---
# To change airports without touching code, set 'TARGET_AIRPORT' in GitHub Vars
SELECTED_KEY = os.getenv("TARGET_AIRPORT", "JFK")
ap = AIRPORTS.get(SELECTED_KEY, AIRPORTS["JFK"])

# Radar sweep range (approx 1 degree = 111km)
BOUNDS = {
    'lamin': ap['lat'] - 0.8, 'lamax': ap['lat'] + 0.8,
    'lomin': ap['lon'] - 0.8, 'lomax': ap['lon'] + 0.8
}

def calculate_dist_3d(p1, p2):
    """Calculates horizontal distance (km) and vertical separation (m)"""
    lon1, lat1 = np.radians(p1['lon']), np.radians(p1['lat'])
    lon2, lat2 = np.radians(p2['lon']), np.radians(p2['lat'])
    
    # Haversine for horizontal distance
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    h_dist = 6371 * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))
    
    # Vertical distance in meters
    v_dist = abs(p1['alt'] - p2['alt'])
    return h_dist, v_dist

def get_live_states():
    url = "https://opensky-network.org/api/states/all"
    headers = {'User-Agent': 'ATC-AI-Agent-Personal-Project'}
    try:
        r = requests.get(url, params=BOUNDS, headers=headers, timeout=20)
        if r.status_code == 200:
            return r.json().get('states', [])
        return []
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []

def run_ai_logic():
    raw_data = get_live_states()
    processed = []

    # --- PHASE 1: DATA CLEANING ---
    for s in raw_data:
        # Index: 0=ICAO, 1=Callsign, 5=Lon, 6=Lat, 7=Alt(m), 11=VertRate, 14=Squawk
        if all(v is not None for v in [s[0], s[5], s[6], s[7]]):
            processed.append({
                "id": s[1].strip() if s[1] else s[0],
                "lat": float(s[6]), "lon": float(s[5]),
                "alt": float(s[7]), "vr": float(s[11]) if s[11] else 0,
                "squawk": s[14], "status": "EN_ROUTE", "color": "cyan", "cmd": ""
            })

    # --- PHASE 2: CLASSIFICATION & SAFETY AI ---
    n = len(processed)
    for i in range(n):
        p = processed[i]
        
        # 1. EMERGENCY/TECH ISSUES (PURPLE)
        if p['squawk'] in ['7700', '7600', '7500']:
            p['status'], p['color'] = "EMERGENCY / TECH ISSUE", "purple"
            p['cmd'] = "Priority landing sequence initiated. Squawk 7700 confirmed."

        # 2. FLIGHT PHASES (WHITE
