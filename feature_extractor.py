import math

class FeatureExtractor:
    def __init__(self, keyword_weights):
        self.weights = keyword_weights

    def get_features(self, mov_A, mov_B):
        """
        Returns feature vector: 
        [Genre, Keyword, Cast, Director, Year, Rating]
        """
        return [
            self.jaccard(mov_A['genres'], mov_B['genres']),
            self.weighted_jaccard(mov_A['keywords'], mov_B['keywords']),
            self.cast_similarity(mov_A['cast'], mov_B['cast']),
            self.jaccard(mov_A['directors'], mov_B['directors']),
            self.year_similarity(mov_A['year'], mov_B['year']),
            self.rating_similarity(mov_A['rating'], mov_B['rating'])
        ]

    # --- HELPERS ---
    def jaccard(self, set_A, set_B):
        if not set_A or not set_B: return 0.0
        intersection = len(set_A.intersection(set_B))
        union = len(set_A.union(set_B))
        return intersection / union if union > 0 else 0.0

    def weighted_jaccard(self, set_A, set_B):
        # set_A contains keyword strings
        intersection = set_A.intersection(set_B)
        union = set_A.union(set_B)
        if not union: return 0.0
        
        num = sum([self.weights.get(k, 0) for k in intersection])
        den = sum([self.weights.get(k, 0) for k in union])
        return num / den if den > 0 else 0.0

    def cast_similarity(self, cast_A, cast_B):
        # cast_A is Dict {'Name': RelevanceScore}
        inter = set(cast_A.keys()).intersection(set(cast_B.keys()))
        union = set(cast_A.keys()).union(set(cast_B.keys()))
        if not union: return 0.0
        
        # Average Numerator / Max Denominator (Fuzzy Set Logic)
        num = sum([(cast_A[a] + cast_B[a])/2 for a in inter]) 
        den = sum([max(cast_A.get(a,0), cast_B.get(a,0)) for a in union])
        return num / den if den > 0 else 0.0

    def year_similarity(self, yA, yB):
        if yA == 0 or yB == 0: return 0.0
        diff = abs(yA - yB)
        # Gaussian Decay: Strict on eras
        # A 10-year gap results in ~0.36 similarity
        return math.exp(-(diff**2) / 100.0)

    def rating_similarity(self, rA, rB):
        if rA == 0 or rB == 0: return 0.0
        diff = abs(rA - rB)
        return max(0.0, 1.0 - (diff / 10.0))