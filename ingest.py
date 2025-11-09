"""
Ask My Docs — Auto-Ingest Watcher (with OCR)
--------------------------------------------
Continuously monitors your 'docs/' folder for new or updated PDFs
and automatically ingests them into ChromaDB using Ollama embeddings.
Now includes intelligent OCR fallback for scanned or image-based PDFs.

🧠 Goal:
Hands-free local document intelligence — drop PDFs in, and they’re instantly available for chat.
"""

import os
import time
import json
import tempfile
from pathlib import Path
from pypdf import PdfReader
from ollama import Client
import chromadb
from tqdm import tqdm
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ocrmypdf  # 🧠 OCR engine wrapper for Tesseract

# --- CONFIGURATION ---
DOCS_DIR = Path("docs")
DB_DIR = Path("db")
STATE_FILE = DB_DIR / "ingest_state.json"
COLLECTION_NAME = "documents"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNK_SLEEP = 0.05  # ⏳ small delay per chunk to reduce CPU heat

# --- INITIAL SETUP ---
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

print("🔧 Initializing Ask My Docs — Auto-Ingest Mode (with OCR)...\n")

# --- Initialize Ollama + ChromaDB ---
try:
    client = Client()
    client.list()  # Verify Ollama server is active
except Exception:
    print("❌ Ollama server not responding. Please run `ollama serve` first.")
    raise SystemExit(1)

try:
    chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
except Exception as e:
    print(f"❌ Failed to initialize ChromaDB: {e}")
    raise SystemExit(1)


# --- STATE MANAGEMENT ---
def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# --- PDF HANDLING ---
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Attempt to extract text directly using PyPDF."""
    try:
        reader = PdfReader(pdf_path)
        return "".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as e:
        print(f"⚠️ Error reading {pdf_path.name}: {e}")
        return ""


def run_ocr_if_needed(pdf_path: Path) -> Path:
    """
    Runs OCR if the file contains no extractable text.
    Returns path to the OCR’d version (in temp folder) or original path.
    """
    text = extract_text_from_pdf(pdf_path)
    if text:
        return pdf_path  # already has selectable text

    print(f"🧠 Running OCR on {pdf_path.name} (scanned or image-based PDF)...")
    start_time = time.time()
    tmp_dir = Path(tempfile.gettempdir())
    ocr_path = tmp_dir / f"ocr_{pdf_path.stem}.pdf"

    try:
        ocrmypdf.ocr(
            str(pdf_path),
            str(ocr_path),
            deskew=True,
            skip_text=True,  # skip pages that already have text
            progress_bar=False,
        )
        print(f"✅ OCR complete ({time.time() - start_time:.1f}s): {ocr_path.name}")
        return ocr_path
    except Exception as e:
        print(f"❌ OCR failed for {pdf_path.name}: {e}")
        return pdf_path  # fallback gracefully


def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks for robust embedding coverage."""
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def embed_text(chunk: str):
    """Generate embeddings locally via Ollama."""
    try:
        response = client.embeddings(model=EMBED_MODEL, prompt=chunk)
        return response["embedding"]
    except Exception as e:
        print(f"⚠️ Embedding failed: {e}")
        return None


# --- CORE INGESTION LOGIC ---
def ingest_single_pdf(pdf_path: Path):
    """
    Extract, OCR if needed, chunk, embed, and store a single PDF in ChromaDB.
    Skips already-ingested or up-to-date files.
    """
    state = load_state()
    mtime = pdf_path.stat().st_mtime

    # Skip if already processed and not modified
    if state.get(pdf_path.name, 0) >= mtime:
        print(f"⏩ {pdf_path.name} already up-to-date. Skipping.")
        return

    # OCR check
    readable_pdf = run_ocr_if_needed(pdf_path)
    text = extract_text_from_pdf(readable_pdf)

    if not text:
        print(f"⚠️ Skipping {pdf_path.name} (no readable text even after OCR).")
        return

    print(f"\n➡️ Ingesting new/updated file: {pdf_path.name}")
    chunks = chunk_text(text)
    print(f"   ↳ Split into {len(chunks)} chunks.\n")

    new_chunks = 0
    for i, chunk in enumerate(tqdm(chunks, desc="   Embedding chunks", unit="chunk")):
        embedding = embed_text(chunk)
        if not embedding:
            continue

        doc_id = f"{pdf_path.stem}::chunk_{i}"
        existing = collection.get(ids=[doc_id])
        if existing and existing["ids"]:
            continue  # Skip duplicates

        metadata = {
            "filename": pdf_path.name,
            "chunk_index": i,
            "timestamp": time.time(),
        }

        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[metadata],
        )

        new_chunks += 1
        time.sleep(CHUNK_SLEEP)  # 🌡️ throttle slightly for lower heat

    # Persist state
    state[pdf_path.name] = mtime
    save_state(state)

    print(f"✅ {pdf_path.name} ingested ({new_chunks} new chunks).")
    print(f"🧠 ChromaDB size: {collection.count()} entries\n")


# --- WATCHDOG HANDLER ---
class PDFEventHandler(FileSystemEventHandler):
    """Watches for new or modified PDFs and triggers ingestion."""

    def on_created(self, event):
        if event.src_path.endswith(".pdf"):
            time.sleep(1)  # wait for file copy to finish
            ingest_single_pdf(Path(event.src_path))

    def on_modified(self, event):
        if event.src_path.endswith(".pdf"):
            time.sleep(1)
            ingest_single_pdf(Path(event.src_path))


# --- MAIN LOOP ---
def watch_folder():
    """Continuously watch for new/updated PDFs and trigger ingestion."""
    print(f"👀 Watching folder: {DOCS_DIR.resolve()}")
    print("📂 Drop PDFs here — they’ll be automatically processed.\n")

    event_handler = PDFEventHandler()
    observer = Observer()
    observer.schedule(event_handler, str(DOCS_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping watcher. Goodbye!")
        observer.stop()
    observer.join()


# --- ENTRY POINT ---
if __name__ == "__main__":
    watch_folder()
