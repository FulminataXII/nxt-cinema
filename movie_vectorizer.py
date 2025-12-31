import json
import math
import pickle

# --- CONFIG ---
RAW_DATA_FILE = "tmdb_10k_movies_detailed.json"
WEIGHTS_FILE = "keyword_weights.pkl"
OUTPUT_VECTORS_FILE = "movie_vectors.pkl"

def load_weights():
    try:
        with open(WEIGHTS_FILE, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print("Error: Weights file not found. Run build_weights.py first!")
        return None

def process_movie(raw_movie, weights_dict):
    """
    Transforms raw JSON into a math-optimized Python object.
    """
    # 1. Cast: Apply Rank Decay (1 / sqrt(order + 1))
    cast_dict = {}
    for actor in raw_movie.get('cast', []):
        name = actor['name']
        order = actor['order']
        # We cap the decay so the 10th actor doesn't get 0, but it gets small
        score = 1.0 / math.sqrt(order + 1)
        cast_dict[name] = score

    # 2. Keywords: Filter and Store
    # Optimization: We ONLY store keywords that exist in our weights file.
    # If a new keyword appears that wasn't in the training set, we ignore it 
    # (or you could assign a default high rarity).
    valid_keywords = set()
    for k in raw_movie.get('keywords', []):
        if k in weights_dict:
            valid_keywords.add(k)
            
    # 3. Directors & Genres: Standard Sets
    directors_set = set(raw_movie.get('directors', []))
    genres_set = set(raw_movie.get('genres', []))

    # Return the clean object
    return {
        "id": raw_movie['id'],
        "title": raw_movie['title'],
        "year": int(raw_movie['year']) if str(raw_movie['year']).isdigit() else 0,
        "rating": float(raw_movie['rating']),
        "keywords": valid_keywords, # Set of strings
        "cast": cast_dict,          # Dict {'Name': Score}
        "directors": directors_set, # Set of strings
        "genres": genres_set        # Set of strings
    }

def main():
    # 1. Load Resources
    weights = load_weights()
    if not weights: return

    try:
        with open(RAW_DATA_FILE, 'r') as f:
            raw_movies = json.load(f)
    except FileNotFoundError:
        print(f"Error: {RAW_DATA_FILE} not found.")
        return

    # 2. Vectorize
    print(f"Vectorizing {len(raw_movies)} movies...")
    processed_data = []
    
    for movie in raw_movies:
        vec = process_movie(movie, weights)
        processed_data.append(vec)

    # 3. Save
    # We save ONLY the movies list. The weights are already safe in the other file.
    with open(OUTPUT_VECTORS_FILE, 'wb') as f:
        pickle.dump(processed_data, f)

    print(f"SUCCESS: Processed movie vectors saved to {OUTPUT_VECTORS_FILE}")

if __name__ == "__main__":
    main()