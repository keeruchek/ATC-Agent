import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# 1. Load & Clean OurAirports Data
# Ensure you have downloaded airports.csv from ourairports.com/data/
df = pd.read_csv('airports.csv')
df = df[df['type'].str.contains('airport', na=False)] # Keep only actual airports

# 2. Initialize Neural Model
model = SentenceTransformer('all-MiniLM-L6-v2')

def build_vector_db():
    # We combine Name, City, and Country into a single "meaning" string
    metadata = (df['name'] + " " + df['municipality'] + " " + df['iso_country']).fillna('')
    embeddings = model.encode(metadata.tolist(), show_progress_bar=True)
    
    # 3. Create FAISS Vector Index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    
    return index, df

def neural_search(query, index, df, k=1):
    query_vec = model.encode([query])
    distances, indices = index.search(np.array(query_vec).astype('float32'), k)
    
    match = df.iloc[indices[0][0]]
    return {
        "name": match['name'],
        "lat": match['latitude_deg'],
        "lon": match['longitude_deg'],
        "icao": match['ident']
    }
