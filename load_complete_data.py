import pandas as pd
import requests
import json
import time
import os

# --- CONFIGURATION ---
API_KEY = "bd03c37f1e75ca781769cd6007dfcee4"
INPUT_CSV = "tmdb_10k_movies.csv"
OUTPUT_JSON = "tmdb_10k_movies_detailed.json"

def fetch_movie_details(movie_id, session):
    """
    Fetches full details for a single movie using append_to_response.
    Gets: Basic Info + Credits (Cast/Crew) + Keywords
    """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {
        "api_key": API_KEY,
        "append_to_response": "credits,keywords", # THE MAGIC PARAMETER
        "language": "en-US"
    }
    
    try:
        response = session.get(url, params=params)
        
        # Handle Rate Limiting (429)
        if response.status_code == 429:
            print("Rate limit hit! Sleeping for 5 seconds...")
            time.sleep(5)
            return fetch_movie_details(movie_id, session) # Retry
            
        if response.status_code != 200:
            print(f"Error {response.status_code} for ID {movie_id}")
            return None
            
        data = response.json()
        
        # --- PARSE THE DATA IMMEDIATELY TO SAVE SPACE ---
        
        # 1. Extract Director
        crew = data.get('credits', {}).get('crew', [])
        directors = [member['name'] for member in crew if member['job'] == 'Director']
        
        # 2. Extract Top 10 Cast (with Order)
        cast_raw = data.get('credits', {}).get('cast', [])
        # We only keep top 10 to save space, but keep 'order' for your weighting logic
        top_cast = [
            {'name': member['name'], 'order': member['order']} 
            for member in cast_raw[:10]
        ]
        
        # 3. Extract Keywords
        keywords = [k['name'] for k in data.get('keywords', {}).get('keywords', [])]
        
        return {
            "id": data['id'],
            "title": data['title'],
            "year": data.get('release_date', '')[:4], # Extract just the year
            "rating": data['vote_average'],
            "vote_count": data['vote_count'],
            "genres": [g['name'] for g in data.get('genres', [])],
            "keywords": keywords,
            "cast": top_cast,
            "directors": directors
        }

    except Exception as e:
        print(f"Exception for ID {movie_id}: {e}")
        return None

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if API_KEY == "YOUR_TMDB_API_KEY_HERE":
        print("ERROR: Please insert your API Key.")
    else:
        # 1. Load the IDs from Part 1
        if not os.path.exists(INPUT_CSV):
            print(f"Error: {INPUT_CSV} not found. Run Part 1 script first.")
        else:
            df = pd.read_csv(INPUT_CSV)
            movie_ids = df['id'].tolist()
            
            print(f"Loaded {len(movie_ids)} movie IDs to fetch.")
            
            detailed_data = []
            session = requests.Session()
            
            # 2. Loop and Fetch
            # Note: 10,000 requests will take time. 
            # TMDB allows ~40 requests per 10 seconds.
            
            start_time = time.time()
            
            for i, mid in enumerate(movie_ids):
                details = fetch_movie_details(mid, session)
                if details:
                    detailed_data.append(details)
                
                # Progress Bar
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"Processed {i + 1}/{len(movie_ids)} movies. Time: {elapsed:.2f}s")
                    
                    # Periodic Save (Safety check)
                    with open(OUTPUT_JSON, 'w') as f:
                        json.dump(detailed_data, f)
                
                # Polite Sleep (approx 30-40 req/sec max)
                time.sleep(0.26) 

            # 3. Final Save
            with open(OUTPUT_JSON, 'w') as f:
                json.dump(detailed_data, f)
            
            print(f"DONE! Full dataset saved to {OUTPUT_JSON}")