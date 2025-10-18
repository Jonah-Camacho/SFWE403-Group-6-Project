# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, List

# Import your advisor functions from ChatBot.py
from ChatBot import advisor_turn, advisor_sources

class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    history: List[Msg] = []
    new_session: bool = False
    k_ctx: int = 5

app = FastAPI(title="UA SE Advisor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    hist = [{"role": m.role, "content": m.content} for m in req.history][-24:]
    reply = advisor_turn(hist, new_session=req.new_session, k_ctx=req.k_ctx)
    return {"reply": reply}