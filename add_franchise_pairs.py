import requests
import json
import pandas as pd
import time
import os

# --- CONFIGURATION ---
API_KEY = "NOTHING_TO_SEE_HERE"
MOVIES_JSON = "tmdb_10k_movies_detailed.json"
TRAINING_CSV = "training_pairs.csv"
MOVIES_TO_SCAN = 3000  # Scans top 3000 to catch sequels/prequels

def get_franchise_pairs(movie_ids):
    session = requests.Session()
    collections = {} # {collection_id: [movie_id_1, movie_id_2]}
    
    print(f"Scanning top {len(movie_ids)} movies for franchise data...")
    
    for i, mid in enumerate(movie_ids):
        url = f"https://api.themoviedb.org/3/movie/{mid}"
        try:
            r = session.get(url, params={"api_key": API_KEY})
            if r.status_code == 200:
                data = r.json()
                collection = data.get('belongs_to_collection')
                
                if collection:
                    cid = collection['id']
                    if cid not in collections:
                        collections[cid] = []
                    collections[cid].append(mid)
                    
            elif r.status_code == 429:
                time.sleep(1)
        except: pass
        
        if (i + 1) % 100 == 0:
            print(f"Scanned {i + 1}/{len(movie_ids)}...")
        
        time.sleep(0.02) 

    # Generate Pairs
    pairs = []
    print("\nGenerating pairs...")
    for cid, mids in collections.items():
        if len(mids) < 2: continue
        
        for i in range(len(mids)):
            for j in range(i + 1, len(mids)):
                pairs.append({
                    "movie_A": mids[i],
                    "movie_B": mids[j],
                    "target": 1
                })
                
    print(f"Found {len(pairs)} franchise pairs from {len(collections)} collections.")
    return pairs

if __name__ == "__main__":
    if API_KEY == "NOTHING_TO_SEE_HERE":
        print("ERROR: Please set your API Key.")
    else:
        if not os.path.exists(MOVIES_JSON):
            print("Movies JSON not found.")
        else:
            # 1. Load Candidate IDs
            with open(MOVIES_JSON, 'r') as f:
                movies = json.load(f)
            
            top_ids = [m['id'] for m in movies[:MOVIES_TO_SCAN]]
            
            # 2. Find New Pairs
            franchise_pairs = get_franchise_pairs(top_ids)
            
            if franchise_pairs:
                # 3. Append to CSV
                df_new = pd.DataFrame(franchise_pairs)
                header = not os.path.exists(TRAINING_CSV)
                
                # Append to the bottom
                df_new.to_csv(TRAINING_CSV, mode='a', header=header, index=False)
                print(f"Appended {len(df_new)} new pairs.")
                
                # 4. THE SHUFFLE STEP
                print("Shuffling the final dataset...")
                df_full = pd.read_csv(TRAINING_CSV)
                
                # sample(frac=1) returns a random sample of the whole dataframe (shuffling it)
                df_shuffled = df_full.sample(frac=1).reset_index(drop=True)
                
                # Overwrite the file
                df_shuffled.to_csv(TRAINING_CSV, index=False)
                
                print(f"SUCCESS: {TRAINING_CSV} updated. Total pairs: {len(df_shuffled)} (Shuffled)")
            else:
                print("No franchise pairs found.")