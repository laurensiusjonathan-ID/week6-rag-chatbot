# store.py — one place for client + model
from qdrant_client import QdrantClient, models
 
MODEL = "BAAI/bge-small-en-v1.5"
client = QdrantClient(path="./qdrant_data")
 
def ensure_collection(name: str) -> None:
    if not client.collection_exists(name):
        client.create_collection(name,
            vectors_config=models.VectorParams(
                size=client.get_embedding_size(MODEL),
                distance=models.Distance.COSINE))
