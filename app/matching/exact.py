from app.normalization import normalize

def match_exact(query: str, in_memory_data: list) -> list:
    query_norm = normalize(query)
    results = []
    
    for ent in in_memory_data:
        canon_norm = normalize(ent["canonical_name"])
        if query_norm == canon_norm:
            results.append((ent["entity_id"], 1.0, ent["canonical_name"], "canonical_name", None))
            continue
            
        for alias in ent["aliases"]:
            if query_norm == normalize(alias):
                results.append((ent["entity_id"], 1.0, ent["canonical_name"], "alias", alias))
                break # Only need one match per entity
                
    return results