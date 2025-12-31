import json
import math
import pickle
from collections import Counter

# --- CONFIG ---
INPUT_FILE = "tmdb_10k_movies_detailed.json"
OUTPUT_WEIGHTS_FILE = "keyword_weights.pkl"

def build_normalized_weights():
    print("Loading raw data.")
    try:
        with open(INPUT_FILE, 'r') as f:
            raw_movies = json.load(f)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    total_movies = len(raw_movies)
    keyword_counts = Counter()

    # 1. Count Frequencies
    print(f"Scanning {total_movies} movies...")
    for m in raw_movies:
        # We use a set to avoid double counting if a keyword appears twice in one movie description
        unique_kws = set(m.get('keywords', []))
        for k in unique_kws:
            keyword_counts[k] += 1

    # 2. Calculate Normalized IDF
    # Max possible IDF is when a word appears in only 1 movie: log(1 + total/1)
    max_idf = math.log(1 + total_movies)
    
    normalized_weights = {}
    
    print("Calculating normalized scores...")
    for word, count in keyword_counts.items():
        # Your Formula
        raw_idf = math.log(1 + (total_movies / count))
        normalized_score = raw_idf / max_idf
        normalized_weights[word] = normalized_score
        print({word, normalized_score})

    # 3. Save
    print(f"Saving {len(normalized_weights)} keyword weights...")
    with open(OUTPUT_WEIGHTS_FILE, 'wb') as f:
        pickle.dump(normalized_weights, f)
        
    print(f"SUCCESS: Weights saved to {OUTPUT_WEIGHTS_FILE}")

if __name__ == "__main__":
    build_normalized_weights()