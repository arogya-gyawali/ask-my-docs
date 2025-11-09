import chromadb
from ollama import Client
from textwrap import shorten
from pathlib import Path

# --- CONFIG ---
DB_DIR = Path("db")
COLLECTION_NAME = "documents"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.1:8b"
TOP_K = 4
MAX_CONTEXT_CHARS = 4000

# --- SETUP ---
print("🔧 Initializing Ask My Docs (Local RAG Mode)...\n")

try:
    client = Client()
    client.list()  # ensures Ollama is active
except Exception:
    print("❌ Ollama server not responding. Start it with: `ollama serve`.")
    raise SystemExit(1)

try:
    chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
except Exception as e:
    print(f"❌ Failed to connect to ChromaDB: {e}")
    raise SystemExit(1)

if collection.count() == 0:
    print("⚠️ Your database is empty! Run `ingest.py` first to add PDFs.")
    raise SystemExit(1)


def retrieve_context(query, top_k=TOP_K):
    """Retrieve top-k relevant chunks for the given query."""
    try:
        q_embed = client.embeddings(model=EMBED_MODEL, prompt=query)["embedding"]
        results = collection.query(query_embeddings=[q_embed], n_results=top_k)
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        return docs, metas
    except Exception as e:
        print(f"⚠️ Retrieval failed: {e}")
        return [], []


def truncate_context(chunks, max_chars=MAX_CONTEXT_CHARS):
    """Concatenate chunks up to a safe character limit."""
    context = ""
    for chunk in chunks:
        if len(context) + len(chunk) > max_chars:
            break
        context += chunk + "\n\n"
    return context.strip()


def ask_my_docs(query, show_context=False):
    """Ask a question and get an answer grounded in your documents."""
    docs, metas = retrieve_context(query)
    if not docs:
        print("⚠️ No relevant documents found.")
        return ""

    context = truncate_context(docs)
    prompt = f"""You are a helpful assistant.
Use the provided context to answer accurately and concisely.

Context:
{context}

Question: {query}
Answer:"""

    try:
        response = client.chat(model=CHAT_MODEL, messages=[{"role": "user", "content": prompt}])
        answer = response["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ Chat failed: {e}")
        return ""

    print("\n🧠 Question:", query)
    print("💬 Answer:", answer)

    if show_context:
        print("\n📄 Top retrieved chunks (truncated):")
        for m, d in zip(metas, docs):
            print(f"- {m['filename']} [chunk {m['chunk_index']}] → {shorten(d, 150)}")

    return answer


if __name__ == "__main__":
    print("🔎 Ask My Docs — Local RAG Mode")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            q = input("❓ Enter your question: ").strip()
            if q.lower() in {"exit", "quit"}:
                print("👋 Goodbye!")
                break
            ask_my_docs(q, show_context=True)
            print("-" * 60)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
