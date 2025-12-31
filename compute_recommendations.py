import sqlite3
import pickle
import pandas as pd
import numpy as np
import time
import heapq
from feature_extractor import FeatureExtractor

# --- CONFIG ---
MOVIES_FILE = "movie_vectors.pkl"
WEIGHTS_FILE = "learned_weights.pkl"
KEYWORD_W_FILE = "keyword_weights.pkl"
DB_FILE = "recommendations.db"
TOP_K = 25

def compute():
    print("Loading resources...")
    movies = pickle.load(open(MOVIES_FILE, "rb"))
    learned_weights = pickle.load(open(WEIGHTS_FILE, "rb"))
    keyword_weights = pickle.load(open(KEYWORD_W_FILE, "rb"))
    
    extractor = FeatureExtractor(keyword_weights)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS preds")
    c.execute("CREATE TABLE preds (source_id INTEGER, target_id INTEGER, score REAL)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_source ON preds (source_id)")
    
    print("Building lookup maps...")
    movies_map = {m['id']: m for m in movies}
    all_ids = list(movies_map.keys())
    
    print(f"Computing recommendations for {len(all_ids)} movies...")
    start_time = time.time()
    batch_data = []
    
    # Pre-fetch weights for speed
    w_genre = learned_weights.get('Genres', 0)
    w_key = learned_weights.get('Keywords', 0)
    w_cast = learned_weights.get('Cast', 0)
    w_dir = learned_weights.get('Director', 0)
    w_year = learned_weights.get('Year', 0)
    w_rate = learned_weights.get('Rating', 0)

    for i, source_id in enumerate(all_ids):
        source_movie = movies_map[source_id]
        
        # The Min-Heap to store Top K
        # Stores tuples: (score, target_id)
        # We use a Min-Heap so heap[0] is always the lowest score we've accepted so far.
        top_k_heap = []
        
        for target_id in all_ids:
            if source_id == target_id: continue
            
            target_movie = movies_map[target_id]
            
            # Optimization: Pre-filter (Genre Disjoint)
            # If genres don't overlap, score is usually too low to beat Top 20.
            # (Remove this check if you want cross-genre discovery)
            if not source_movie['genres'].intersection(target_movie['genres']):
                continue

            feats = extractor.get_features(source_movie, target_movie)
            
            final_score = (
                feats[0] * w_genre +
                feats[1] * w_key +
                feats[2] * w_cast +
                feats[3] * w_dir +
                feats[4] * w_year +
                feats[5] * w_rate
            )
            
            # --- HEAP LOGIC ---
            if len(top_k_heap) < TOP_K:
                # If heap isn't full, just push
                heapq.heappush(top_k_heap, (final_score, target_id))
            else:
                # If heap is full, check if new score is better than the worst in heap
                if final_score > top_k_heap[0][0]:
                    # Replace the smallest element with this new one
                    heapq.heapreplace(top_k_heap, (final_score, target_id))
        
        # After loop, top_k_heap has the best items, but in heap order.
        # Sort them descending for final storage.
        top_k_sorted = sorted(top_k_heap, key=lambda x: x[0], reverse=True)
        
        for score, tid in top_k_sorted:
            # Threshold check: Don't save garbage even if it made the Top 20
            
            batch_data.append((source_id, tid, score))
            if score < 0.05:
                print("Found in top 25, score < 0.05")
            
        if len(batch_data) > 10000:
            c.executemany("INSERT INTO preds VALUES (?,?,?)", batch_data)
            conn.commit()
            batch_data = []
            print(f"Processed {i+1}/{len(all_ids)} movies... ({(time.time()-start_time)/60:.1f} min)")

    if batch_data:
        c.executemany("INSERT INTO preds VALUES (?,?,?)", batch_data)
        conn.commit()
        
    conn.close()
    print("Done! Database ready.")

if __name__ == "__main__":
    compute()