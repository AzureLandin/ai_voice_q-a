from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime


class HistoryResponse(BaseModel):
    session_id: str
    history: List[Message]


class WSMessage(BaseModel):
    type: Literal["text", "audio_ready", "error"]
    text: Optional[str] = None
    error: Optional[str] = None
