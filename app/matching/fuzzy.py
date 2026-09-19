from rapidfuzz.distance import JaroWinkler, Levenshtein
from app.normalization import normalize

def match_fuzzy(query: str, in_memory_data: list) -> list:
    query_norm = normalize(query)
    results = []
    
    for ent in in_memory_data:
        best_score = 0.0
        best_jw = 0.0
        best_lev = 0.0
        best_type = None
        best_alias = None
        
        canon_norm = normalize(ent["canonical_name"])
        jw = JaroWinkler.normalized_similarity(query_norm, canon_norm)
        lev = Levenshtein.normalized_similarity(query_norm, canon_norm)
        score = max(jw, lev)
        
        if score > best_score:
            best_score = score
            best_jw = jw
            best_lev = lev
            best_type = "canonical_name"
            
        for alias in ent["aliases"]:
            alias_norm = normalize(alias)
            jw_a = JaroWinkler.normalized_similarity(query_norm, alias_norm)
            lev_a = Levenshtein.normalized_similarity(query_norm, alias_norm)
            score_a = max(jw_a, lev_a)
            
            if score_a > best_score:
                best_score = score_a
                best_jw = jw_a
                best_lev = lev_a
                best_type = "alias"
                best_alias = alias
                
        if best_score >= 0.65: # Only return plausible fuzzy matches
            results.append((ent["entity_id"], best_score, best_jw, best_lev, ent["canonical_name"], best_type, best_alias))
            
    # Return top 5
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:5]