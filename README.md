# 🧠 Ask My Docs  
*A fully local, privacy-first document assistant powered by Ollama + ChromaDB + Streamlit.*

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-green.svg)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-orange.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-App_UI-red.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

---

## 🚀 Overview
**Ask My Docs** lets you *chat with your own PDFs—completely offline.*  
It combines **Ollama**’s local LLMs with **ChromaDB** vector search and a **Streamlit** interface to make documents instantly searchable and conversational.

🔒 **Private · Local · Free** — No internet, no cloud, no hidden APIs.

---

## ✨ Features
- 🧠 100 % **local processing** — zero API calls or external dependencies  
- 📄 **Multi-PDF ingestion** with automatic text extraction  
- 🔍 **Semantic search** powered by ChromaDB  
- 💬 **Interactive Q&A** via Streamlit chat interface  
- 💾 **Persistent local database** for instant re-use  
- ⚡ Lightweight setup — runs on a MacBook Air  

---

## 🧰 Tech Stack

| Layer | Technology | Purpose |
|:------|:------------|:---------|
| 🐍 Backend | **Python 3.11+** | Core scripting and orchestration |
| 🦙 LLM | **Ollama** | Local embeddings + model inference |
| 🧩 Vector DB | **ChromaDB** | Document indexing & semantic retrieval |
| 📚 Parsing | **PyPDF** | Extracts text from PDF pages |
| 🌈 UI | **Streamlit** | Browser-based local interface |

---

## 🗂️ Folder Structure
```text
ask-my-docs/
├── docs/         # 📚 Your PDF files
├── db/           # 💾 Local ChromaDB storage (auto-generated)
├── ingest.py     # 🧠 Embedding & ingestion script
├── app.py        # 💬 Streamlit chat interface (optional)
├── README.md     # 📘 Project documentation
└── .gitignore    # ⚙️ Ignored files / folders
````

---

## ⚙️ Installation (macOS)

```bash
# Clone the repository
cd ~/Desktop/Projects
git clone https://github.com/<yourusername>/ask-my-docs.git
cd ask-my-docs

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -U pip
pip install chromadb pypdf streamlit ollama
```

---

## 🦙 Ollama Setup

Ensure **Ollama** is installed and running locally.

```bash
# Start Ollama server
ollama serve &
# Pull models
ollama pull nomic-embed-text     # Embedding model
ollama pull llama3.1:8b          # Optional chat model
```

✅ **Test embeddings**

```bash
python3 - <<'PY'
from ollama import Client
c = Client()
print("✅ Embedding length:", len(c.embeddings(
    model="nomic-embed-text", prompt="Hello world")["embedding"]))
PY
```

Expected: `✅ Embedding length: 768`

---

## 🧩 Usage

1. Place PDFs inside `docs/`.
2. Generate embeddings and store them:

   ```bash
   python3 ingest.py
   ```
3. *(Optional)* Launch the Streamlit app:

   ```bash
   streamlit run app.py
   ```
4. Open your browser → [http://localhost:8501](http://localhost:8501)

Ask naturally:

> “Summarize section 3 of contract.pdf.”
> “Compare key findings between report A and report B.”

---

## 🧠 Example Commands

**Rebuild embeddings**

```bash
rm -rf db && python3 ingest.py
```

**Inspect ChromaDB collections**

```bash
python3 - <<'PY'
import chromadb
client = chromadb.PersistentClient(path="db")
print(client.list_collections())
PY
```

---

## 🤝 Contributing

Contributions and ideas are welcome!
Please ensure:

* Clear, descriptive commit messages
* Updated README when adding new dependencies or features

---

## 🪶 Commit & Branch Conventions

**Commit messages**

```
feat: add Streamlit chat UI  
fix: handle blank PDF pages  
docs: improve setup instructions  
chore: update .gitignore  
```

**Branch names**

```
feat/streamlit-ui
fix/pdf-extraction
docs/readme-update
```

**Example workflow**

```bash
git checkout -b feat/improve-chunking
# make changes
git add .
git commit -m "feat(ingest): improve text chunking overlap"
git push -u origin feat/improve-chunking
```

---

## 🧾 License

MIT License © 2025 Aarogya Gyawali

---

> 💬 *“Your documents. Your machine. Your answers — locally.”*

```
```
