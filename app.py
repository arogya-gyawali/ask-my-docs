import streamlit as st
import chromadb
from pathlib import Path
from rag_pipeline import ask_my_docs, retrieve_context

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ask My Docs 🧠", page_icon="🧠", layout="wide")

# --- INITIAL SETUP ---
DB_DIR = Path("db")
COLLECTION_NAME = "documents"

try:
    chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    num_docs = collection.count()
except Exception as e:
    st.error(f"❌ Could not connect to ChromaDB: {e}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("📂 Project Info")
st.sidebar.markdown("**Ask My Docs** — Local RAG assistant using Ollama + ChromaDB.")
st.sidebar.markdown(f"📄 **Indexed Chunks:** `{num_docs}`")
st.sidebar.markdown(f"💾 **Database Path:** `{DB_DIR.resolve()}`")
st.sidebar.markdown("🧠 **Models:**\n- `nomic-embed-text`\n- `llama3.1:8b`")
st.sidebar.divider()
st.sidebar.markdown("💬 Type a question below to get started!")

# --- MAIN CHAT AREA ---
st.title("🧠 Ask My Docs — Local Chat Assistant")
st.caption("Chat with your PDFs locally. 100% offline. Zero cloud, zero cost.")

if num_docs == 0:
    st.warning("⚠️ No documents indexed yet. Please run `ingest.py` first.")
    st.stop()

# --- SESSION STATE (persistent chat history) ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- DISPLAY PREVIOUS CHAT HISTORY ---
for q, a in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        st.markdown(a)

# --- CHAT INPUT ---
query = st.chat_input("Ask a question about your documents...")

if query:
    # Only append new query if it’s different from the last one
    if not st.session_state.history or st.session_state.history[-1][0] != query:
        with st.chat_message("user"):
            st.markdown(query)

        with st.spinner("💭 Thinking..."):
            try:
                answer = ask_my_docs(query)
            except Exception as e:
                st.error(f"⚠️ Model error: {e}")
                st.stop()

        st.session_state.history.append((query, answer))

        with st.chat_message("assistant"):
            st.markdown(answer)

# --- DEBUG MODE ---
with st.expander("🧩 Show Retrieved Context (Debug Mode)"):
    if st.session_state.history:
        last_query = st.session_state.history[-1][0]
        try:
            docs, metas = retrieve_context(last_query)
            st.subheader("📄 Retrieved Chunks:")
            for m, d in zip(metas, docs):
                st.markdown(f"**{m['filename']}** (chunk {m['chunk_index']}):")
                st.code(d[:600] + ("..." if len(d) > 600 else ""), language="markdown")
        except Exception as e:
            st.error(f"⚠️ Failed to fetch context: {e}")
