import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from common.embedding import embed_text  # noqa: E402

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
VECTOR_INDEX_PATH = PROCESSED_DIR / "vector_index.json"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def load_documents(raw_dir: Path) -> Iterable[Path]:
    for path in raw_dir.glob("**/*"):
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
            yield path


def process_document(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    metadata = {
        "source": str(path.relative_to(RAW_DIR)),
        "url": f"file://{path.resolve()}",
        "date": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "title": path.stem,
    }
    return {
        "document": metadata["source"],
        "chunks": [
            {"text": chunk, "metadata": metadata}
            for chunk in chunks
        ],
    }


def save_processed(doc: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{Path(doc['document']).stem}.json"
    output_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {output_path}")


def build_vector_index(processed_dir: Path, output_path: Path) -> None:
    entries = []
    for doc_path in processed_dir.glob("*.json"):
        data = json.loads(doc_path.read_text(encoding="utf-8"))
        for chunk in data.get("chunks", []):
            text = chunk.get("text", "")
            metadata = chunk.get("metadata", {})
            metadata.setdefault("title", doc_path.stem)
            metadata.setdefault("url", f"file://{doc_path.resolve()}")
            metadata.setdefault("date", datetime.utcnow().isoformat())
            embedding = embed_text(text)
            entries.append({
                "embedding": embedding,
                "text": text,
                "metadata": metadata,
            })

    if not entries:
        print("No processed chunks available to build the vector index.")
        return

    output_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Vector index saved to {output_path}")


def run_pipeline() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw directory not found: {RAW_DIR}")

    documents = list(load_documents(RAW_DIR))
    if not documents:
        print("No documents found in data/raw/. Add .txt or .md files to ingest.")
        return

    for path in documents:
        processed = process_document(path)
        save_processed(processed, PROCESSED_DIR)

    build_vector_index(PROCESSED_DIR, VECTOR_INDEX_PATH)


if __name__ == "__main__":
    run_pipeline()
