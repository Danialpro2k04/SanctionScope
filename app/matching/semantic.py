from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Load globally to avoid reload on every request
q_client = QdrantClient(host="localhost", port=6333)
encoder = SentenceTransformer("intfloat/multilingual-e5-small")

def match_semantic(query: str) -> list:
    vector = encoder.encode(query).tolist()
    
    hits = q_client.search(
        collection_name="sanctions_entities",
        query_vector=vector,
        limit=20
    )
    
    # Aggregate to one result per entity (MAX score)
    best_per_entity = {}
    for hit in hits:
        eid = hit.payload["entity_id"]
        if eid not in best_per_entity or hit.score > best_per_entity[eid]["score"]:
            alias_val = hit.payload["text"] if hit.payload["text_type"] == "alias" else None
            best_per_entity[eid] = {
                "score": hit.score,
                "matched_text": hit.payload["text"] if hit.payload["text_type"] == "canonical_name" else "See alias",
                "matched_on": hit.payload["text_type"],
                "matched_alias_text": alias_val
            }
            
    results = []
    for eid, data in best_per_entity.items():
        results.append((eid, data["score"], data["matched_text"], data["matched_on"], data["matched_alias_text"]))
        
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:5]