import requests
import json
import random
import pandas as pd
import time
import os

# --- CONFIGURATION ---
API_KEY = "NOTHING_TO_SEE_HERE"
INPUT_FILE = "tmdb_10k_movies_detailed.json"
OUTPUT_FILE = "training_pairs.csv"
NUM_SOURCE_MOVIES = 500

def load_movies_as_dict(filepath):
    if not os.path.exists(filepath):
        print(f"ERROR: {filepath} not found.")
        return {}
    
    with open(filepath, 'r') as f:
        movies = json.load(f)
    
    movie_lookup = {}
    for m in movies:
        movie_lookup[m['id']] = {
            'genres': set(m.get('genres', [])),
            'cast': set([c['name'] for c in m.get('cast', [])]),
            'keywords': set(m.get('keywords', [])) 
        }
    return movie_lookup

def fetch_positive_pairs(movie_ids, api_key):
    positive_pairs = []
    session = requests.Session()
    source_subset = movie_ids[:NUM_SOURCE_MOVIES]
    
    print(f"\n--- Fetching Positive Pairs (Target = 1) ---")
    
    for i, source_id in enumerate(source_subset):
        url = f"https://api.themoviedb.org/3/movie/{source_id}/recommendations"
        try:
            r = session.get(url, params={"api_key": api_key})
            if r.status_code == 200:
                for rec in r.json().get('results', [])[:5]:
                    if rec['id'] in movie_ids: 
                        positive_pairs.append({
                            "movie_A": source_id,
                            "movie_B": rec['id'],
                            "target": 1
                        })
            elif r.status_code == 429:
                time.sleep(1.0) 
        except: pass
        
        if (i + 1) % 50 == 0: 
            print(f"Fetched recommendations for {i + 1}/{len(source_subset)} movies...")
        
        time.sleep(0.02) # Fast sleep as requested
        
    print(f"Collected {len(positive_pairs)} positive pairs.")
    return positive_pairs

def generate_safe_negative_pairs(movie_ids, movie_lookup, target_count):
    print(f"\n--- Generating {target_count} Mixed Negative Pairs ---")
    negative_pairs = []
    
    # We want 50% Easy (Different Genres) and 50% Hard (Same Genre, different Cast)
    target_hard = target_count // 2
    
    while len(negative_pairs) < target_count:
        id_a = random.choice(movie_ids)
        id_b = random.choice(movie_ids)
        if id_a == id_b: continue
            
        data_a = movie_lookup.get(id_a)
        data_b = movie_lookup.get(id_b)
        if not data_a or not data_b: continue
        
        # LOGIC:
        # We ALWAYS require Cast and Keywords to be disjoint (Safe).
        # But we will sometimes ALLOW Genre overlap to create "Hard" examples.
        
        # 1. Cast & Keywords MUST be different (Base Safety)
        if not data_a['cast'].isdisjoint(data_b['cast']) or \
           not data_a['keywords'].isdisjoint(data_b['keywords']):
            continue

        # 2. Decide Type: Hard vs Easy
        is_hard_negative = not data_a['genres'].isdisjoint(data_b['genres'])
        
        # If we still need Hard Negatives (Same Genre), accept this pair.
        if is_hard_negative and (len(negative_pairs) < target_hard):
            negative_pairs.append({"movie_A": id_a, "movie_B": id_b, "target": 0})
            
        # If we need Easy Negatives (Diff Genre), accept this pair.
        elif (not is_hard_negative) and (len(negative_pairs) >= target_hard):
            negative_pairs.append({"movie_A": id_a, "movie_B": id_b, "target": 0})
            
        if len(negative_pairs) % 500 == 0:
            print(f"Generated {len(negative_pairs)} pairs...")

    print(f"Finished. Generated {len(negative_pairs)} negatives.")
    return negative_pairs

if __name__ == "__main__":
    if API_KEY == "NOTHING_TO_SEE_HERE":
        print("ERROR: Please insert your API Key.")
    else:
        movie_lookup = load_movies_as_dict(INPUT_FILE)
        all_ids = list(movie_lookup.keys())
        
        if not all_ids:
            print("No movies found.")
        else:
            pos_data = fetch_positive_pairs(all_ids, API_KEY)
            
            target_negatives = len(pos_data) if len(pos_data) > 0 else 2500
            neg_data = generate_safe_negative_pairs(all_ids, movie_lookup, target_negatives)
            
            full_data = pos_data + neg_data
            random.shuffle(full_data)
            
            df = pd.DataFrame(full_data)
            df.to_csv(OUTPUT_FILE, index=False)
            print(f"\nSUCCESS! Saved {len(df)} pairs to {OUTPUT_FILE}")