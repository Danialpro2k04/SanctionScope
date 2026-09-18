import json
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

# 1. Initialize client with an extended timeout (60 seconds)
client = QdrantClient("http://localhost:6333", timeout=60.0)
model = SentenceTransformer("all-MiniLM-L6-v2")
collection_name = "sanctions"

def load_to_qdrant(json_file_path):
    with open(json_file_path, "r") as f:
        entities = json.load(f)

    # Use recreate_collection for qdrant-client 1.6.4 compatibility
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    print("Embedding points...")
    points = []
    for idx, ent in enumerate(entities):
        vec = model.encode(ent.get("canonical_name", "")).tolist()
        points.append(
            PointStruct(
                id=idx,
                vector=vec,
                payload={
                    "id": ent.get("id", str(idx)),  # Safely falls back to the index
                    "canonical_name": ent.get("canonical_name", ""),
                    "aliases": ent.get("aliases", []),
                    "sanctions": ent.get("sanctions", []),
                },
            )
        )

    # 2. Upload points in smaller batches of 500
    batch_size = 500
    total_points = len(points)
    print(f"Uploading {total_points} points in batches of {batch_size}...")

    for i in range(0, total_points, batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        print(f"Uploaded {min(i + batch_size, total_points)} / {total_points} points")

    print("Successfully loaded all vectors into Qdrant!")

if __name__ == "__main__":
    load_to_qdrant("data/processed_entities.json")