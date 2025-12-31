import pickle
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from feature_extractor import FeatureExtractor

# --- CONFIG ---
MOVIES_FILE = "movie_vectors.pkl"
WEIGHTS_FILE = "keyword_weights.pkl"
TRAINING_DATA = "training_pairs.csv"
OUTPUT_MODEL = "learned_weights.pkl"

def train():
    # 1. Load Resources
    print("Loading resources...")
    try:
        movies_vec = pickle.load(open(MOVIES_FILE, "rb"))
        keyword_weights = pickle.load(open(WEIGHTS_FILE, "rb"))
        training_df = pd.read_csv(TRAINING_DATA)
    except FileNotFoundError as e:
        print(f"Error: Missing file. {e}")
        return

    # Create ID Lookup Map
    movie_map = {m['id']: m for m in movies_vec}
    extractor = FeatureExtractor(keyword_weights)

    X = [] 
    y = [] 
    
    print(f"Processing {len(training_df)} training pairs...")
    
    # 2. Build Feature Vectors
    missing_count = 0
    for index, row in training_df.iterrows():
        id_A = int(row['movie_A'])
        id_B = int(row['movie_B'])
        target = int(row['target'])
        
        if id_A not in movie_map or id_B not in movie_map:
            missing_count += 1
            continue
            
        features = extractor.get_features(movie_map[id_A], movie_map[id_B])
        X.append(features)
        y.append(target)

    if missing_count > 0:
        print(f"Skipped {missing_count} pairs (data missing).")

    # 3. Split & Validate
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- THE FIX: Use LinearRegression ---
    # positive=True forces weights to be non-negative
    # fit_intercept=False forces the bias to be 0 (so 0 similarity input = 0 score)
    clf = LinearRegression(fit_intercept=False, positive=True)
    
    print(f"Training model on {len(X_train)} samples...")
    clf.fit(X_train, y_train)
    
    # Check Accuracy (We threshold at 0.5 since LinearReg returns a float 0.0-1.0)
    raw_preds = clf.predict(X_test)
    binary_preds = [1 if p > 0.5 else 0 for p in raw_preds]
    
    acc = accuracy_score(y_test, binary_preds)
    print(f"\nModel Accuracy: {acc:.2%}")
    print(classification_report(y_test, binary_preds, target_names=['No Match', 'Match']))

    # 4. Final Retrain on ALL Data
    print("Retraining on full dataset for final export...")
    clf.fit(X, y)

    # 5. Extract and Normalize Weights
    feature_names = ['Genres', 'Keywords', 'Cast', 'Director', 'Year', 'Rating']
    coefficients = clf.coef_ # LinearRegression stores weights here
    
    # Handle case where all weights are 0 (rare safety check)
    total = sum(coefficients)
    if total == 0:
        print("WARNING: Model found no correlation. Defaulting to equal weights.")
        coefficients = [1.0] * len(feature_names)
        total = sum(coefficients)

    # Normalize so they sum to 1.0
    final_weights = {name: val/total for name, val in zip(feature_names, coefficients)}

    print("\n" + "="*30)
    print(" FINAL LEARNED WEIGHTS ")
    print("="*30)
    for k, v in final_weights.items():
        print(f"{k.ljust(10)} : {v:.4f}")
    print("="*30)
    
    # Save
    with open(OUTPUT_MODEL, 'wb') as f:
        pickle.dump(final_weights, f)
    print(f"Weights saved to {OUTPUT_MODEL}")

if __name__ == "__main__":
    train()