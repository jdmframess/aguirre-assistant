import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from common.embedding import cosine_similarity, embed_text  # noqa: E402

app = FastAPI(title="Aguirre Assistant Backend")

VECTOR_INDEX_PATH = ROOT / "data" / "processed" / "vector_index.json"
TOP_K = 3


class ChatRequest(BaseModel):
    question: str


class Citation(BaseModel):
    url: Optional[str]
    title: Optional[str]
    retrieved_at: Optional[str]


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]


def load_vector_index() -> List[Dict]:
    if not VECTOR_INDEX_PATH.exists():
        return []
    data = json.loads(VECTOR_INDEX_PATH.read_text(encoding="utf-8"))
    entries = []
    for item in data:
        entries.append(
            {
                "embedding": item.get("embedding", []),
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
            }
        )
    return entries


VECTOR_INDEX = load_vector_index()
VECTOR_INDEX_MTIME: Optional[float] = VECTOR_INDEX_PATH.stat().st_mtime if VECTOR_INDEX_PATH.exists() else None


@app.get("/")
async def read_root():
    return {
        "status": "ok",
        "service": "backend",
        "time": datetime.utcnow().isoformat() + "Z",
        "index_size": len(get_vector_index()),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "index_size": len(get_vector_index())}


def get_vector_index() -> List[Dict]:
    global VECTOR_INDEX, VECTOR_INDEX_MTIME
    if VECTOR_INDEX_PATH.exists():
        mtime = VECTOR_INDEX_PATH.stat().st_mtime
        if VECTOR_INDEX_MTIME != mtime:
            VECTOR_INDEX = load_vector_index()
            VECTOR_INDEX_MTIME = mtime
    return VECTOR_INDEX


def retrieve_similar_chunks(question: str, top_k: int = TOP_K):
    index = get_vector_index()
    if not index:
        raise HTTPException(
            status_code=503,
            detail="Vector index not built yet. Run `make ingest` to build it.",
        )

    query_embedding = embed_text(question)
    scored = []
    for item in index:
        score = cosine_similarity(query_embedding, item["embedding"])
        scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def generate_answer(question: str, contexts: List[str]) -> str:
    if not contexts:
        return "No se encontraron documentos relevantes todavía. Ejecuta `make ingest` para poblar el índice."

    context_preview = "\n".join(f"- {snippet[:250]}" for snippet in contexts)
    return (
        "Aquí tienes una respuesta basada en los fragmentos más relevantes:\n"
        f"{context_preview}\n"
        f"Pregunta: {question}"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    results = retrieve_similar_chunks(body.question)
    contexts = [item["text"] for item in results]
    citations = [
        Citation(
            url=item["metadata"].get("url"),
            title=item["metadata"].get("title"),
            retrieved_at=item["metadata"].get("date"),
        )
        for item in results
    ]
    answer = generate_answer(body.question, contexts)
    return ChatResponse(answer=answer, citations=citations)
