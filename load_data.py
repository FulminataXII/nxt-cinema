import requests
import pandas as pd
import time
import os

# --- CONFIGURATION ---
API_KEY = "NOTHING_TO_SEE_HERE"
OUTPUT_FILE = "tmdb_10k_movies.csv"
TOTAL_PAGES_TO_FETCH = 500  # 500 pages * 20 movies = 10,000 movies

def fetch_movies():
    movies_data = []
    
    # Session is faster for repeated requests
    session = requests.Session()
    
    print(f"Starting fetch for {TOTAL_PAGES_TO_FETCH} pages...")
    
    for page in range(1, TOTAL_PAGES_TO_FETCH + 1):
        url = f"https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": API_KEY,
            "sort_by": "popularity.desc",
            "page": page,
            # We assume English language for consistency, optional
            "language": "en-US", 
            "vote_count.gte": 100, # Filter out movies with very few votes to ensure quality
            "include_adult": "false"
        }
        
        try:
            response = session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for movie in data['results']:
                movies_data.append({
                    "id": movie['id'],
                    "title": movie['title'],
                    "overview": movie['overview'],
                    "release_date": movie.get('release_date', ''),
                    "popularity": movie['popularity'],
                    "vote_average": movie['vote_average'],
                    "vote_count": movie['vote_count'],
                    # Store genre_ids now, we will map them to names later
                    "genre_ids": movie['genre_ids'] 
                })
            
            # Progress marker
            if page % 50 == 0:
                print(f"Fetched {page} pages ({len(movies_data)} movies)...")
                
            # Respect API Rate Limits (TMDB is generous, but safe side)
            time.sleep(0.05)
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    return pd.DataFrame(movies_data)

# --- POST-PROCESSING ---
def get_genre_map(api_key):
    """Fetches the official Genre ID -> Name mapping"""
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}&language=en-US"
    r = requests.get(url)
    genres = r.json()['genres']
    return {g['id']: g['name'] for g in genres}

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if API_KEY == "NOTHING_TO_SEE_HERE":
        print("ERROR: Please insert your actual TMDB API Key in the script.")
    else:
        # 1. Fetch Basic Movie Data
        df = fetch_movies()
        
        # 2. Fetch Genre Mapping and Apply
        print("Mapping genres...")
        genre_map = get_genre_map(API_KEY)
        # Convert list of IDs [28, 12] -> "Action|Adventure" string
        df['genres'] = df['genre_ids'].apply(
            lambda ids: "|".join([genre_map.get(i, '') for i in ids])
        )
        
        # 3. Save to CSV
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"SUCCESS: Saved {len(df)} movies to {OUTPUT_FILE}")