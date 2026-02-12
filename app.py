import os, requests, json, time
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# --- NEURAL ENGINE CONFIG ---
MODEL = SentenceTransformer('all-MiniLM-L6-v2')
AIRPORT_DATA_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"

def get_neural_match(query):
    # 1. Load Data
    if not os.path.exists('airports.csv'):
        print("Downloading Global Airport Database...")
        r = requests.get(AIRPORT_DATA_URL)
        with open('airports.csv', 'wb') as f: f.write(r.content)
    
    df = pd.read_csv('airports.csv')
    df = df[df['type'].str.contains('airport', na=False)].fillna('')
    
    # 2. Semantic Chunking
    chunks = (df['name'] + " " + df['municipality'] + " " + df['iso_country']).tolist()
    
    # 3. Vector Indexing (The "Training" phase)
    embeddings = MODEL.encode(chunks, convert_to_numpy=True)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    
    # 4. Neural Search
    query_vec = MODEL.encode([query], convert_to_numpy=True)
    _, indices = index.search(query_vec.astype('float32'), 1)
    
    match = df.iloc[indices[0][0]]
    return {
        "name": match['name'],
        "lat": float(match['latitude_deg']),
        "lon": float(match['longitude_deg']),
        "icao": match['ident']
    }

# --- ATC AGENT LOGIC ---
def run_agent():
    target_query = os.getenv("TARGET_AIRPORT", "New York JFK")
    ap = get_neural_match(target_query)
    print(f"Neural Agent Focus: {ap['name']} ({ap['icao']})")

    # OpenSky API Fetch
    bbox = {'lamin': ap['lat']-1, 'lamax': ap['lat']+1, 'lomin': ap['lon']-1, 'lomax': ap['lon']+1}
    try:
        r = requests.get("https://opensky-network.org/api/states/all", params=bbox, timeout=15)
        states = r.json().get('states', [])
    except: states = []

    aircraft = []
    for s in states:
        if not s[5] or not s[6]: continue
        alt, vr = s[7] or 0, s[11] or 0
        
        # Color Categorization Logic
        status, color = "EN_ROUTE", "cyan"
        if s[14] in ['7700', '7600']: status, color = "EMERGENCY", "purple"
        elif alt < 600:
            status, color = ("LANDING", "green") if vr < -0.5 else ("TAKEOFF", "white")
        elif alt < 3000 and vr < -1.0: status, color = "READY", "blue"
        
        aircraft.append({
            "id": s[1].strip() or s[0], "lat": s[6], "lon": s[5],
            "alt": alt, "vr": vr, "status": status, "color": color
        })

    with open("data.json", "w") as f:
        json.dump({"airport": ap, "aircraft": aircraft, "time": time.ctime()}, f)

if __name__ == "__main__":
    run_agent()
