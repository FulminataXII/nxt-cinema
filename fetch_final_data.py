import pickle
import requests
import time
import os

# --- CONFIGURATION ---
API_KEY = "NOTHING_TO_SEE_HERE"
INPUT_VECTORS = "movie_vectors.pkl"
OUTPUT_FILE = "movie_data.pkl"

def fetch_and_enrich():
    print("Loading existing vectors...")
    if not os.path.exists(INPUT_VECTORS):
        print(f"Error: {INPUT_VECTORS} not found.")
        return

    # Load the basic data (ID, Title, Year)
    movies_data = pickle.load(open(INPUT_VECTORS, "rb"))
    total_movies = len(movies_data)
    
    print(f"Fetching metadata for {total_movies} movies from TMDB...")
    print("This may take 10-15 minutes depending on your connection.")
    
    session = requests.Session()
    enriched_data = []
    
    start_time = time.time()
    
    for i, movie in enumerate(movies_data):
        movie_id = movie['id']
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        
        try:
            r = session.get(url, params={"api_key": API_KEY, "language": "en-US"})
            
            if r.status_code == 200:
                meta = r.json()
                
                # 1. Get Poster
                poster_path = meta.get('poster_path')
                if poster_path:
                    movie['poster_url'] = f"https://image.tmdb.org/t/p/w200{poster_path}"
                else:
                    # Fallback image
                    movie['poster_url'] = "https://image.tmdb.org/t/p/w200"
                
                # 2. Get Overview (Description)
                overview = meta.get('overview', "")
                movie['overview'] = overview if overview else "No description found on TMDB."
                
                # 3. Create Official Link
                movie['tmdb_url'] = f"https://www.themoviedb.org/movie/{movie_id}"
                
            elif r.status_code == 429:
                # Rate limit hit - reuse old data if possible, or add placeholders
                print(f"Rate limit hit at movie {i}. Sleeping...")
                time.sleep(0.02)
                movie['poster_url'] = "https://via.placeholder.com/200x300?text=Error"
                movie['overview'] = "Could not fetch description."
                movie['tmdb_url'] = f"https://www.themoviedb.org/movie/{movie_id}"
                
            else:
                # Movie might have been deleted from TMDB or ID is wrong
                movie['poster_url'] = "https://via.placeholder.com/200x300?text=Not+Found"
                movie['overview'] = "Description unavailable."
                movie['tmdb_url'] = "#"

        except Exception as e:
            print(f"Error fetching {movie_id}: {e}")
        
        # Add to new list
        enriched_data.append(movie)
        
        # Progress Log
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = (total_movies - (i + 1)) / rate / 60
            print(f"Processed {i + 1}/{total_movies} movies... (~{remaining:.1f} mins left)")
        
        # Respect API Rate Limits (40-50 reqs/sec is usually safe)
        time.sleep(0.02)

    # Save Final File
    print(f"\nSaving enriched data to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'wb') as f:
        pickle.dump(enriched_data, f)
    
    print("Done! You can now run your Flask app.")

if __name__ == "__main__":
    if API_KEY == "NOTHING_TO_SEE_HERE":
        print("ERROR: Please set your API Key inside the script.")
    else:
        fetch_and_enrich()