import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import ollama
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from langdetect import detect, LangDetectException

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# -----------------------------------------------------------------------------
# Configuration (env-first; with reasonable defaults)
# -----------------------------------------------------------------------------
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM", "gemma3:12b")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ragdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")  # <- change or use env var

# How many chunks to pull from Postgres per query
TOP_K = int(os.getenv("TOP_K", "25"))

# How long a chat can be idle before we reset history
INACTIVITY_TIMEOUT = timedelta(minutes=3)


# -----------------------------------------------------------------------------
# FastAPI setup
# -----------------------------------------------------------------------------
app = FastAPI(title="ChatCat RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    reply: str


# -----------------------------------------------------------------------------
# Database connection pool
# -----------------------------------------------------------------------------
db_pool: Optional[SimpleConnectionPool] = None


def get_db_pool() -> SimpleConnectionPool:
    """
    Lazily initialize a global connection pool.
    """
    global db_pool
    if db_pool is None:
        db_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    return db_pool


def run_query(sql: str, params: tuple) -> List[Dict]:
    """
    Helper to run a SELECT query and return rows as dicts.
    """
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        pool.putconn(conn)


# -----------------------------------------------------------------------------
# Conversation state & timeout handling
# -----------------------------------------------------------------------------
class ConversationState:
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.last_activity: datetime = datetime.utcnow()


conversations: Dict[str, ConversationState] = {}


def get_conversation(chat_id: str) -> ConversationState:
    """
    Get or create a conversation. If it has been idle longer than the
    INACTIVITY_TIMEOUT, reset its history.
    """
    now = datetime.utcnow()
    state = conversations.get(chat_id)

    if state is None:
        state = ConversationState()
        conversations[chat_id] = state
        return state

    # Check inactivity timeout
    if now - state.last_activity > INACTIVITY_TIMEOUT:
        # Reset history on timeout
        state.messages = []

    state.last_activity = now
    return state


# -----------------------------------------------------------------------------
# Embedding + Retrieval
# -----------------------------------------------------------------------------
def get_embedding(text: str) -> List[float]:
    """
    Get an embedding vector for a piece of text using Ollama.
    """
    try:
        resp = ollama.embeddings(model=EMBED_MODEL, prompt=text)
        return resp["embedding"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting embedding from model '{EMBED_MODEL}': {e}",
        )


def retrieve_relevant_chunks(query: str, k: int = TOP_K) -> List[Dict]:
    """
    Embed the query and retrieve the top-k most similar chunks from Postgres
    using pgvector's <-> distance operator.
    """
    query_emb = get_embedding(query)

    sql = """
        SELECT
            source_id,
            chunk_id,
            content,
            metadata
        FROM rag_chunks
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
    """
    rows = run_query(sql, (query_emb, k))
    return rows


# -----------------------------------------------------------------------------
# LLM call
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are ChatCat, a helpful assistant for the University of Arizona
Software Engineering program.

SCOPE (VERY IMPORTANT)
- You ONLY answer questions about:
  - UA Software Engineering BS, MS, and PhD programs
  - Courses, curriculum, prerequisites, and technical electives
  - Admissions, application steps, transfer credit, and registration
  - Tuition, fees, financial aid, and scholarships for SE students
  - Advisors, research opportunities, careers, and related UA resources
- If a question is NOT clearly about these topics (for example:
  food, sports, opinions, weather, generic programming questions, 
  or personal life questions), you MUST NOT answer it directly.

OFF-TOPIC HANDLING
- For any off-topic or irrelevant question, respond with a short
  fallback such as:
  "I’m here to help with Software Engineering at the University of
   Arizona. I can’t answer that question, but I’d be happy to help
   with degree programs, courses, admissions, or advising."
- Do NOT try to be helpful on the off-topic subject itself.
- Do NOT give opinions, trivia, or general chit-chat that is unrelated
  to UA Software Engineering.
  
STYLE & FORMATTING
- Always answer in clear, concise English.
- Start with a 1–2 sentence high-level summary.
- Then break the answer into sections with short headings (e.g., "Overview",
  "Typical 8-Semester Plan", "Math & Science Requirements", "Next Steps").
- Use bullet points and short lists instead of long paragraphs when listing
  courses or requirements.
- Never paste large tables or raw markdown from the context. Instead, rewrite
  them as clean bullet lists by semester or topic.
- Give an in-depth bullet point summary of each topic for multi-part questions.
- Refrain from using "must have" for requriements, instead use passive language.
- Provide appropriate web links at the end of each response to where they can find the information.
- Limit responses to under 2000 words.

CONTEXT HANDLING
- You will sometimes receive extra information called "context".
- You MUST NOT mention "context", "documents", or "the information you shared"
  in your answer. Just speak directly to the student.
- Prefer facts that appear in the context when they are relevant.
- If the context does not contain some detail the student asked for, you may
  use your own general knowledge to fill in the gap instead of saying that
  the information is missing.

TUITION, FEES, AND TIME-SENSITIVE DETAILS
- If the student asks for tuition, fees, or other dollar amounts and those
  numbers are NOT clearly present in the context, you should:
  - Give a reasonable approximate answer based on your general knowledge
    (e.g., typical ranges for a public university like UA).
  - Clearly say that the exact amount can change and they should confirm with
    the official UA tuition page or bursar's office.
- Do NOT say that the documents do not list the tuition; just answer with an
  approximate value and a verification reminder.

EXTRA CONTEXT
- SAT and ACT scores are not required.
- transfer student admissions does not require any specific classes to have been completed.

GUARDRAILS
- If you're genuinely unsure even with general knowledge, say you are not
  completely sure and suggest who the student can contact.
- Be conservative when guessing details; do not confidently invent specific
  course codes or highly precise numbers that aren't in the context.
- do not store or use personally identifiable information even if given to you by the user.
- do NOT accept off topic questions and do NOT answer them.
"""


def build_context_block(chunks: List[Dict]) -> str:
    """
    Turn retrieved DB chunks into a context string for the LLM.
    """
    parts = []
    for ch in chunks:
        src = ch.get("source_id", "unknown_source")
        cid = ch.get("chunk_id", "")
        content = ch.get("content", "")
        parts.append(f"[{src} / {cid}]\n{content}")
    return "\n\n---\n\n".join(parts)


def call_llm_with_rag(user_question: str, chunks: List[Dict]) -> str:
    """
    Call the LLM with a system prompt, an optional context block, and the user question.
    The model is allowed to improvise using general knowledge when the context
    is incomplete, but should not talk about the context explicitly.
    """
    context_block = build_context_block(chunks)

    # If we retrieved anything at all, we still treat this as "with context".
    if context_block.strip():
        prompt = (
            "You are answering a question about the University of Arizona "
            "Software Engineering program.\n\n"
            "Here is some background information that may or may not contain "
            "everything needed to fully answer the question:\n"
            "do not answer off topic questions not about U of A.\n"
            f"{context_block}\n\n"
            "User question:\n"
            f"{user_question}\n\n"
            "Instructions:\n"
            "1. Use any relevant facts from the background information above,\n"
            "   but do NOT copy it verbatim.\n"
            "2. If some detail (such as an exact tuition amount) is not clearly\n"
            "   present in that background, answer using your own general\n"
            "   knowledge instead of saying that the information is missing.\n"
            "3. You MUST NOT mention the words 'context', 'documents', or any\n"
            "   phrases like 'the information you shared' in your answer.\n"
            "4. Follow this output format:\n"
            "   - Start with a short 1–2 sentence summary that directly answers\n"
            "     the question.\n"
            "   - Then create at most 3 sections with short headings such as:\n"
            "       * Overview\n"
            "       * Details\n"
            "       * Next Steps\n"
            "   - Under each heading, use short bullet points ('- ').\n"
            "   - Keep the total response under about 2000 words.\n"
            "5. For tuition and other time-sensitive dollar amounts, give a\n"
            "   reasonable approximate answer and remind the student to verify\n"
            "   the exact value with official UA sources.\n"
            "6. Provide links to relevant websites for the information provided.\n"
        )
    else:
        # No context at all: pure general-knowledge answer
        prompt = (
            "There is no additional background information for this question.\n\n"
            "do not answer off topic questions not about U of A.\n"
            "User question:\n"
            f"{user_question}\n\n"
            "Instructions:\n"
            "- Answer based on your general knowledge as ChatCat, the UA\n"
            "  Software Engineering advisor.\n"
            "- Use headings and bullet lists for clarity.\n"
            "- For tuition, fees, and other time-sensitive details, provide\n"
            "  a reasonable approximate answer and remind the student to\n"
            "  confirm with official UA sources.\n"
        )

    try:
        resp = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return resp["message"]["content"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calling LLM '{LLM_MODEL}': {e}",
        )


# -----------------------------------------------------------------------------
# English-only enforcement
# -----------------------------------------------------------------------------
def is_english(text: str) -> bool:
    """
    Return True if the text appears to be English. If detection fails,
    we treat it as non-English to be safe.
    """
    try:
        lang = detect(text)
        return lang == "en"
    except LangDetectException:
        return False


# -----------------------------------------------------------------------------
# API endpoint
# -----------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest) -> ChatResponse:
    user_message = req.message.strip()
    chat_id = req.chat_id or "default"

    if not user_message:
        return ChatResponse(reply="")

    # English-only gate (or comment out if you’re still debugging)
    if not is_english(user_message):
        return ChatResponse(reply="")

    state = get_conversation(chat_id)

    # RAG retrieval
    chunks = retrieve_relevant_chunks(user_message, k=TOP_K)

    # LLM call
    answer = call_llm_with_rag(user_message, chunks)

    state.messages.append({"role": "user", "content": user_message})
    state.messages.append({"role": "assistant", "content": answer})

    return ChatResponse(reply=answer)