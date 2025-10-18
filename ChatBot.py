import re, yaml, numpy as np, tiktoken
import ollama
import os, json
import os, sys
import psycopg
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime

# -----------------------------
# Models
# -----------------------------
EMBED_MODEL = "nomic-embed-text"
LLM = "gemma3:1b"

# -----------------------------
# System Prompts (RAG-aware)
# -----------------------------
SYSTEM_ASSISTANT = """
You are the University of Arizona Software Engineering Degree Advisor chatbot.
There is no need to intially greet the user, just begin by answering their questions.

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

# -----------------------------
# Local knowledge base
# -----------------------------
BASE_PATH = Path(__file__).parent / "ChatBot.md"
if not BASE_PATH.exists():
    raise FileNotFoundError(f"Knowledge file not found at: {BASE_PATH.resolve()}")

doc_text = BASE_PATH.read_text(encoding="utf-8")

# -----------------------------
# Tokenizer utilities
# -----------------------------
enc = tiktoken.get_encoding("cl100k_base")
def tokens(s: str) -> int:
    return len(enc.encode(s))

def split_by_headings(md: str):
    # Split on H2/H3 boundaries to keep sections semantically meaningful
    parts = re.split(r"(?m)^##\s+|^###\s+", md)
    return [p.strip() for p in parts if p.strip()]

def smart_chunk(md: str, max_tokens=500, overlap=50):
  
    raw = split_by_headings(md)
    chunks = []
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
                    # add token-overlap
                    back = enc.decode(enc.encode(" ".join(cur))[-overlap:])
                    cur = back.split() if back else []
                    cur_tokens = tokens(" ".join(cur))
                cur.append(w)
                cur_tokens += tw
            if cur:
                chunks.append(" ".join(cur))
    return chunks

chunks = smart_chunk(doc_text, max_tokens=450, overlap=60)

# -----------------------------
# Embeddings (normalized for cosine)
# -----------------------------
def embed_batch(texts):
    vecs = []
    for t in texts:
        e = ollama.embeddings(model=EMBED_MODEL, prompt=t)["embedding"]
        vecs.append(np.array(e, dtype=np.float32))
    arr = np.vstack(vecs) if vecs else np.zeros((0,1), dtype=np.float32)
    arr /= (np.linalg.norm(arr, axis=1, keepdims=True) + 1e-9)
    return arr

chunk_vecs = embed_batch(chunks)

def retrieve(query: str, k=5):
    q = np.array(ollama.embeddings(model=EMBED_MODEL, prompt=query)["embedding"], dtype=np.float32)
    q /= (np.linalg.norm(q) + 1e-9)
    sims = chunk_vecs @ q
    idx = np.argsort(-sims)[:k]
    return [(float(sims[i]), chunks[i]) for i in idx]

# -----------------------------
# Conversational helpers
# -----------------------------
def build_context_block(history, k_ctx=5):

    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "software engineering program info")
    last_assistant = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), "")

    # Ask the LLM to craft a tight retrieval query
    rq = ollama.chat(
        model=LLM,
        messages=[
            {"role":"system", "content": SYSTEM_RETRIEVER},
            {"role":"user", "content": f"AssistantPrev: {last_assistant}\nUser: {last_user}"}
        ]
    )["message"]["content"].strip()

    # Fallback: if the retriever got too fancy/empty
    retrieval_query = rq if rq else (last_assistant + " " + last_user).strip()

    ctx = retrieve(retrieval_query, k=k_ctx)
    context_block = "\n\n---\n".join([c for _, c in ctx]) if ctx else ""
    return context_block

def advisor_turn(history, new_session=False, k_ctx=5):
    if new_session or not any(m["role"] == "user" for m in history):
        # Start fresh: generic opening based on context that tends to be universally helpful
        ctx = retrieve("overview of UA software engineering program, admissions, curriculum, advising, costs", k=k_ctx)
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

    # Normal turn: answer the user using top-k retrieved chunks
    context_block = build_context_block(history, k_ctx=k_ctx)
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    messages = [
        {"role":"system", "content": SYSTEM_ASSISTANT},
        {"role":"user", "content":
         "CONTEXT:\n"
         f"{context_block}\n\n"
         f"USER QUESTION:\n{last_user}\n\n"
         "TASK:\n"
         "- Answer directly and concisely using ONLY the CONTEXT above.\n"
         "- If a detail is not in CONTEXT, say so and suggest a concrete next step.\n"
         "- End with a short 'Next steps' list (1–3 bullets) when useful.\n"}
    ]
    return ollama.chat(model=LLM, messages=messages)["message"]["content"].strip()


def advisor_sources(history, k_ctx=5):
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    ctx = retrieve(last_user or "overview UA software engineering", k=k_ctx)
    # Heuristic: extract first line as a "heading-ish" clue
    headings = []
    for _, chunk in ctx:
        first_line = chunk.splitlines()[0].strip()
        # Trim very long lines
        if len(first_line) > 120:
            first_line = first_line[:117] + "..."
        headings.append(f"- {first_line}")
    return "Sources (from your local doc):\n" + "\n".join(headings)


# -----------------------------
# CLI Runner
# -----------------------------
def run_chat():
    print("UA Software Engineering Advisor\n"
          "Commands: /start, /end, /sources\n")
    history = []
    started = False

    while True:
        try:
            user_in = input("> ").strip()

            if user_in.lower() == "/end":
                print("Session ended.")
                break

            if user_in.lower() == "/start":
                started = True
                history = []
                reply = advisor_turn(history, new_session=True)
                print(f"\nAdvisor: {reply}\n")
                history.append({"role":"assistant","content":reply})
                continue

            if not started:
                print('Type "/start" to begin.')
                continue


            if user_in.lower() == "/sources":
                s = advisor_sources(history)
                print(f"\n{s}\n")
                continue

            # User message
            history.append({"role":"user","content":user_in})
            if len(history) > 24:
                history = history[-24:]  # keep context compact

            # Assistant reply
            reply = advisor_turn(history)
            print(f"\nAdvisor: {reply}\n")
            history.append({"role":"assistant","content":reply})

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted.")
            break


# -----------------------------
# Entrypoint
# -----------------------------
if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Loading knowledge from: {BASE_PATH}")
    run_chat()