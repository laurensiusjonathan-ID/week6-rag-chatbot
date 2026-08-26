from store import client, models
from store import MODEL as EMBED_MODEL
from config import API_KEY, BASE_URL_ANTHROPIC, MODEL
import anthropic
 
SYSTEM = (
  "Answer ONLY from the numbered sources provided. "
  "Cite like [1] or [2][3] after each claim. "
  "If the sources do not contain the answer, reply exactly: "
  "'I don't have that in the knowledge base.' "
  "Never use outside knowledge.")


def call_llm(user: str, system: str = SYSTEM,
            max_tokens: int = 800, temperature: float = 0) -> str:
    llm = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL_ANTHROPIC)
    resp = llm.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        # SDK v1.0.0 removed temperature from the signature;
        # pass it through the raw body instead.
        extra_body={"temperature": temperature},
    )
    return resp.content[0].text
 
def answer(q: str) -> tuple[str, list]:
    hits = client.query_points("kb",
        query=models.Document(text=q, model=EMBED_MODEL),
        limit=5).points
    context = "\n\n".join(
        f"[{i+1}] ({h.payload['source']} #{h.payload['chunk']})"
        f"\n{h.payload['text']}" for i, h in enumerate(hits))
    reply = call_llm(system=SYSTEM, max_tokens=700,
        user=f"Sources:\n{context}\n\nQuestion: {q}")
    return reply, hits


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:])
    a, hits = answer(q)
    print(f"=== Question ===\n{q}\n")
    print(f"=== Answer ===\n{a}\n")
    print("=== Sources ===")
    for i, h in enumerate(hits):
        print(f"[{i+1}] ({h.payload['source']} #{h.payload['chunk']})")
        print(h.payload['text'])
        print()
    client.close()