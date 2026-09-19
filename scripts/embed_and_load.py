import json
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

# Must match app/matching/semantic.py exactly: same collection name and same model,
# otherwise query vectors are not comparable to the stored vectors.
client = QdrantClient("http://localhost:6333", timeout=60.0)
model = SentenceTransformer("intfloat/multilingual-e5-small")
collection_name = "sanctions_entities"


def load_to_qdrant(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        entities = json.load(f)

    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    print("Embedding canonical names and aliases...")
    # Embed the canonical name AND every alias as separate points, so a query in
    # any script/language/translation can match directly against the closest
    # known text for that entity. semantic.py aggregates back to one best score
    # per entity_id, so having multiple points per entity is expected.
    texts_to_embed = []
    for ent in entities:
        entity_id = ent["entity_id"]
        canonical = ent.get("canonical_name", "")
        if canonical:
            texts_to_embed.append({
                "entity_id": entity_id,
                "text": canonical,
                "text_type": "canonical_name",
            })
        for alias in ent.get("aliases", []):
            if alias:
                texts_to_embed.append({
                    "entity_id": entity_id,
                    "text": alias,
                    "text_type": "alias",
                })

    print(f"Total texts to embed (canonical + aliases): {len(texts_to_embed)}")

    batch_size = 500
    total = len(texts_to_embed)
    point_id = 0
    for i in range(0, total, batch_size):
        batch = texts_to_embed[i : i + batch_size]
        vectors = model.encode([item["text"] for item in batch]).tolist()

        points = []
        for item, vec in zip(batch, vectors):
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vec,
                    payload={
                        "entity_id": item["entity_id"],
                        "text": item["text"],
                        "text_type": item["text_type"],
                    },
                )
            )
            point_id += 1

        client.upsert(collection_name=collection_name, points=points)
        print(f"Uploaded {min(i + batch_size, total)} / {total} texts")

    print("Successfully loaded all vectors into Qdrant!")


if __name__ == "__main__":
    load_to_qdrant("data/processed_entities.json")