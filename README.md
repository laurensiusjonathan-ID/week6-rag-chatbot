# week6-rag-chatbot

RAG chatbot end-to-end: chunk → embed → store (Qdrant) → retrieve → cited answer.

## Pipeline

```
corpus/*.txt ──> chunker.py ──> ingest.py ──> Qdrant ("kb") <── rag.py <── question
                 (350 tok,        (stable ids,     │
                  50 overlap)      upsert)         └──> LLM ──> answer with [n] citations
```

## Idempotence proof (acceptance criterion)

Ingestion is safe to re-run. Each chunk's point id is derived deterministically
from its source file and chunk index — `md5("{filename}:{chunk_index}")` — so the
same chunk always maps to the **same id**. Qdrant's `upsert` overwrites points by
id instead of appending, so a second run updates the exact same 45 points rather
than duplicating them.

Proof — ingestion run twice in a row, collection count checked after each run:

```
> python ingest.py
ingested 45 chunks
total points in collection: 45
> python ingest.py
ingested 45 chunks
total points in collection: 45
```

The count stays **45** after both runs. If the ids were random (e.g. `uuid4()`),
the second run would have doubled the collection to 90 — the classic
"corpus indexed three times" RAG bug. Stable ids + upsert make re-ingestion
idempotent for free.