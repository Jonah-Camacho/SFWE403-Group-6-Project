import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Literal, Optional, Tuple

import numpy as np
import tiktoken
import ollama

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# -----------------------------------------------------------------------------
# Configuration (env-first; safe defaults)
# -----------------------------------------------------------------------------
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM         = os.getenv("LLM", "gemma3:1b")
DOC_PATH    = os.getenv("CHATBOT_DOC_PATH", r"F:\SFWE403-Group-6-Project\ChatBot.md")
MAX_TOKENS  = int(os.getenv("MAX_CHUNK_TOKENS", "450"))
OVERLAP_TOK = int(os.getenv("CHUNK_OVERLAP_TOKENS", "60"))

# If your Ollama server is not at the default, uncomment and set:
# os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11434"


# -----------------------------------------------------------------------------
# System prompts
# -----------------------------------------------------------------------------
SYSTEM_ASSISTANT = """
You are the University of Arizona Software Engineering Degree Advisor chatbot.

GOAL
- Help prospective and current students understand UA Software Engineering options (e.g., BS/BA/BAS; online vs. in-person), admission requirements, transfer credit, prerequisite chains, curriculum maps, course sequencing, key policies, timelines, tuition/fees and aid, advising and contacts, and typical career outcomes.
- Always answer using ONLY the provided CONTEXT (snippets from the local handbook/notes).
- If a requested detail is not present in CONTEXT, say so briefly and suggest a next step (advising email/office, official catalog, or submitting an official transfer evaluation)—do NOT invent details.

STYLE
- Be concise and structured: short paragraphs and bullet points when helpful.
- Where relevant, add a tiny “Next steps” section with 1–3 actionable items.
- If you cite something from the context, reference the section title or heading in plain text (e.g., “See: ‘Admission Requirements’”)—no external links here.

GUARDRAILS
- Do not assume up-to-date tuition/policy dates if CONTEXT doesn’t include them—state that students should verify with the official UA sources.
- If the user asks questions outside Software Engineering degree info (e.g., unrelated campus facts), answer briefly only if CONTEXT includes it; otherwise, say you don’t have it in the docs and suggest where to check.
"""

SYSTEM_RETRIEVER = """
Given the user’s last message and (optionally) the previous assistant reply, create a focused retrieval query emphasizing:
- program type (BS/BA/BAS/online/in-person), admissions, prerequisites, transfer, curriculum, sequencing, policies, timelines, costs/aid, advising, outcomes, student support.
Return ONLY the refined retrieval query text. No extra commentary.
"""


# -----------------------------------------------------------------------------
# Tokenizer + chunking
# -----------------------------------------------------------------------------
enc = tiktoken.get_encoding("cl100k_base")

def tokens(s: str) -> int:
    return len(enc.encode(s))

def split_by_headings(md: str) -> List[str]:
    # Split on H2/H3 so chunks align to sections
    parts = re.split(r"(?m)^##\s+|^###\s+", md)
    return [p.strip() for p in parts if p.strip()]

def smart_chunk(md: str, max_tokens=500, overlap=50) -> List[str]:
    raw = split_by_headings(md)
    chunks: List[str] = []
    for part in raw:
        if tokens(part) <= max_tokens:
            chunks.append(part)
        else:
            words = part.split()
            cur, cur_tokens = [], 0
            for w in words:
                tw = tokens(w + " ")
                if cur_tokens + tw > max_tokens:
                    chunks.append(" ".join(cur))
                    # token overlap
                    back = enc.decode(enc.encode(" ".join(cur))[-overlap:])
                    cur = back.split() if back else []
                    cur_tokens = tokens(" ".join(cur))
                cur.append(w)
                cur_tokens += tw
            if cur:
                chunks.append(" ".join(cur))
    return chunks


# -----------------------------------------------------------------------------
# Embeddings + retrieval
# -----------------------------------------------------------------------------
def embed_batch(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)
    vecs = []
    for t in texts:
        e = ollama.embeddings(model=EMBED_MODEL, prompt=t)["embedding"]
        v = np.asarray(e, dtype=np.float32)
        v /= (np.linalg.norm(v) + 1e-9)  # normalize for cosine
        vecs.append(v)
    return np.vstack(vecs)

def retrieve(query: str, chunk_vecs: np.ndarray, chunks: List[str], k=5) -> List[Tuple[float, str]]:
    if chunk_vecs.size == 0 or not chunks:
        return []
    q = np.array(ollama.embeddings(model=EMBED_MODEL, prompt=query)["embedding"], dtype=np.float32)
    q /= (np.linalg.norm(q) + 1e-9)
    sims = chunk_vecs @ q
    idx = np.argsort(-sims)[:k]
    return [(float(sims[i]), chunks[i]) for i in idx]


# -----------------------------------------------------------------------------
# Conversational helpers
# -----------------------------------------------------------------------------
def build_context_block(history: List[dict], chunks: List[str], chunk_vecs: np.ndarray, k_ctx=5) -> str:
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "software engineering program info")
    last_assistant = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), "")

    # LLM crafts a focused retrieval query
    rq = ollama.chat(
        model=LLM,
        messages=[
            {"role": "system", "content": SYSTEM_RETRIEVER},
            {"role": "user", "content": f"AssistantPrev: {last_assistant}\nUser: {last_user}"}
        ]
    )["message"]["content"].strip()

    retrieval_query = rq if rq else (last_assistant + " " + last_user).strip()
    ctx = retrieve(retrieval_query, chunk_vecs, chunks, k=k_ctx)
    return "\n\n---\n".join([c for _, c in ctx]) if ctx else ""

def advisor_turn(history: List[dict], chunks: List[str], chunk_vecs: np.ndarray, new_session=False, k_ctx=5) -> str:
    if new_session or not any(m["role"] == "user" for m in history):
        ctx = retrieve(
            "overview of UA software engineering program, admissions, curriculum, advising, costs",
            chunk_vecs, chunks, k=k_ctx
        )
        context_block = "\n\n---\n".join([c for _, c in ctx]) if ctx else ""
        messages = [
            {"role": "system", "content": SYSTEM_ASSISTANT},
            {"role": "user", "content":
                "CONTEXT:\n"
                f"{context_block}\n\n"
                "Start a friendly, concise welcome as the UA Software Engineering Degree Advisor. "
                "Offer help with admissions, transfer credits, curriculum planning, timelines, and advising. "
                "Ask what they’re looking for."}
        ]
        return ollama.chat(model=LLM, messages=messages)["message"]["content"].strip()

    context_block = build_context_block(history, chunks, chunk_vecs, k_ctx=k_ctx)
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    messages = [
        {"role": "system", "content": SYSTEM_ASSISTANT},
        {"role": "user", "content":
            "CONTEXT:\n"
            f"{context_block}\n\n"
            f"USER QUESTION:\n{last_user}\n\n"
            "TASK:\n"
            "- Answer directly and concisely using ONLY the CONTEXT above.\n"
            "- If a detail is not in CONTEXT, say so and suggest a concrete next step.\n"
            "- End with a short 'Next steps' list (1–3 bullets) when useful.\n"}
    ]
    return ollama.chat(model=LLM, messages=messages)["message"]["content"].strip()

def advisor_sources(history: List[dict], chunks: List[str], chunk_vecs: np.ndarray, k_ctx=5) -> str:
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    ctx = retrieve(last_user or "overview UA software engineering", chunk_vecs, chunks, k=k_ctx)
    headings = []
    for _, chunk in ctx:
        first_line = chunk.splitlines()[0].strip()
        headings.append(f"- {first_line[:117] + '...' if len(first_line) > 120 else first_line}")
    return "Sources (from your local doc):\n" + "\n".join(headings)


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(title="UA SE Advisor API")

# Allow React dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",  # Vite
        "http://localhost:3000", "http://127.0.0.1:3000",  # CRA
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (simple attributes; avoid type-annotating app.state for older Pylance)
app.state.chunks = []
app.state.chunk_vecs = np.zeros((0, 1), dtype=np.float32)
app.state.doc_path = Path(DOC_PATH).expanduser()


# -----------------------------
# Pydantic models
# -----------------------------
class HistoryMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    message: Optional[str] = None
    history: Optional[List[HistoryMessage]] = None
    new_session: bool = False
    k_ctx: int = 5

class SourcesRequest(BaseModel):
    history: Optional[List[HistoryMessage]] = None
    k_ctx: int = 5


# -----------------------------
# Startup: load + embed once
# -----------------------------
@app.on_event("startup")
def startup_load_and_embed():
    p = app.state.doc_path
    if not p.exists():
        raise RuntimeError(f"Knowledge file not found at: {p}")
    text = p.read_text(encoding="utf-8")

    chunks = smart_chunk(text, max_tokens=MAX_TOKENS, overlap=OVERLAP_TOK)
    chunk_vecs = embed_batch(chunks)

    app.state.chunks = chunks
    app.state.chunk_vecs = chunk_vecs
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Loaded {len(chunks)} chunks from {p}")


# -----------------------------
# Routes
# -----------------------------
@app.get("/api/health")
def health():
    return {
        "ok": True,
        "models": {"embed": EMBED_MODEL, "llm": LLM},
        "chunks": len(app.state.chunks),
        "doc_path": str(app.state.doc_path),
        "time": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
    }

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        history = [m.dict() for m in (req.history or [])]

        if req.message:
            history.append({"role": "user", "content": req.message})

        if len(history) > 24:
            history = history[-24:]

        reply = advisor_turn(
            history=history,
            chunks=app.state.chunks,
            chunk_vecs=app.state.chunk_vecs,
            new_session=req.new_session,
            k_ctx=req.k_ctx,
        )
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sources")
def sources(req: SourcesRequest):
    try:
        history = [m.dict() for m in (req.history or [])]
        src = advisor_sources(
            history=history,
            chunks=app.state.chunks,
            chunk_vecs=app.state.chunk_vecs,
            k_ctx=req.k_ctx,
        )
        return {"sources": src}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Dev entrypoint
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Starting API. Loading knowledge from: {DOC_PATH}")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)