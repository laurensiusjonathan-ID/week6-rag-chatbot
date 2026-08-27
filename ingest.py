import hashlib
from pathlib import Path
from store import client, models, MODEL, ensure_collection
from chunker import chunk
 
def stable_id(path: str, i: int) -> int:
    h = hashlib.md5(f"{path}:{i}".encode()).hexdigest()
    return int(h[:12], 16)
 
ensure_collection("kb")
points = []
for p in sorted(Path("corpus").glob("*.*")):
    text = p.read_text(errors="ignore")
    for i, ch in enumerate(chunk(text)):
        points.append(models.PointStruct(
            id=stable_id(p.name, i),
            vector=models.Document(text=ch, model=MODEL),
            payload={"text": ch, "source": p.name,
                     "chunk": i}))
client.upsert("kb", points=points)
total = client.count("kb").count
client.close()
print(f"ingested {len(points)} chunks")
print(f"total points in collection: {total}")
