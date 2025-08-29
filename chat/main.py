# main.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RAISC Chat (Dev)")

# --- CORS for local Next.js (proxy or direct) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Simple in-memory store ---
# histories[session_key] = [{"role": "user"|"assistant", "content": str, "ts": ISO8601}, ...]
histories: Dict[str, List[Dict[str, str]]] = {}


class ChatRequest(BaseModel):
    message: str
    session_key: Optional[str] = None  # optional; your UI uses a fixed demo key


class ChatResponse(BaseModel):
    response: str


class HistoryItem(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    chat_history: List[HistoryItem]


def add_msg(session_key: str, role: str, content: str) -> None:
    histories.setdefault(session_key, [])
    histories[session_key].append(
        {"role": role, "content": content, "ts": datetime.utcnow().isoformat()}
    )


def generate_reply(msg: str, history: List[Dict[str, str]]) -> str:
    """
    Lightweight rule-based responder to avoid echoing.
    Adjust/extend with your therapy prompts when ready.
    """
    t = (msg or "").lower().strip()

    # Greetings
    if t in {"hi", "hello", "hey", "salaam", "assalamualaikum", "asalamualaikum"}:
        return "Hi! I’m here to support you. What’s on your mind today?"

    # Quick intents / keywords
    if "anxiety" in t or "panic" in t or "stressed" in t or "stress" in t:
        return (
            "Thanks for sharing that. A quick grounding tip: breathe in 4, hold 4, out 6. "
            "Want to try it together?"
        )
    if "sad" in t or "down" in t or "depressed" in t:
        return "I’m sorry you’re feeling this way. What’s been weighing on you most this week?"

    # Questions
    if t.endswith("?"):
        return "Good question. Tell me a bit more so I can help better."

    # Reflect last user message (not an echo)
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    if last_user:
        return f"It sounds important. What makes “{last_user}” feel most challenging right now?"

    # Default supportive nudge
    return "I’m here with you. What would you like to focus on right now?"


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_key = (req.session_key or "default-session").strip()
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message is required")

    # Save user message
    add_msg(session_key, "user", msg)

    # Generate supportive reply (no echo)
    history = histories.get(session_key, [])
    bot_reply = generate_reply(msg, history)

    # Save assistant message
    add_msg(session_key, "assistant", bot_reply)

    return ChatResponse(response=bot_reply)


@app.get("/api/history/{session_key}", response_model=HistoryResponse)
def get_history(session_key: str):
    items = [
        {"role": item["role"], "content": item["content"]}
        for item in histories.get(session_key, [])
    ]
    return HistoryResponse(chat_history=items)
