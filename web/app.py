from flask import Flask, render_template, request, jsonify
import sqlite3
import pickle

app = Flask(__name__)

# --- LOAD ENRICHED DATA ---
try:
    # CHANGED: Load the final rich dataset
    movies_data = pickle.load(open("web\\movie_data_final.pkl", "rb"))
    
    # Dropdown Options (ID, Title, Poster)
    MOVIE_OPTIONS = [{
        'id': m['id'], 
        'text': f"{m['title']} ({m['year']})",
        'poster': m['poster_url']
    } for m in movies_data]
    
    # Fast Lookup
    MOVIE_LOOKUP = {m['id']: m for m in movies_data}
    
except FileNotFoundError:
    print("Error: movie_data_final.pkl not found. Run create_final_data.py!")
    MOVIE_OPTIONS = []
    MOVIE_LOOKUP = {}

def get_db_connection():
    conn = sqlite3.connect('web\\recommendations.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/movies')
def api_movies():
    return jsonify({'results': MOVIE_OPTIONS})

@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    data = request.json
    source_id = int(data.get('movie_id'))
    
    conn = get_db_connection()
    query = "SELECT target_id, score FROM preds WHERE source_id = ? ORDER BY score DESC LIMIT 10"
    cursor = conn.execute(query, (source_id,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        movie = MOVIE_LOOKUP.get(row['target_id'])
        if movie:
            results.append({
                'title': f"{movie['title']} ({movie['year']})",
                'poster': movie['poster_url'],
                'overview': movie['overview'],    # NEW
                'url': movie['tmdb_url'],         # NEW
                'score': round(row['score'] * 100, 1)
            })
        
    return jsonify({'recommendations': results})

if __name__ == '__main__':
    app.run(debug=True)