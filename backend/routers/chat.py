from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from models.schemas import ChatRequest, ChatResponse, HistoryResponse, Message
from services.ai_service import ai_service
from services.session_service import session_service
from config import TTS_PROVIDER

router = APIRouter(prefix="/api")


class TTSRequest(BaseModel):
    text: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    sid = session_service.get_or_create(req.session_id)
    session_service.add_message(sid, "user", req.question)
    context = session_service.get_context(sid)
    answer = ai_service.ask(context)
    session_service.add_message(sid, "assistant", answer)
    return ChatResponse(answer=answer, session_id=sid)


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    if TTS_PROVIDER != "mimo":
        return Response(content=b"", media_type="audio/wav")
    from services.tts_service import get_tts_service
    tts = get_tts_service()
    audio_bytes = tts.synthesize(req.text)
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/tts/stream")
async def text_to_speech_stream(req: TTSRequest):
    if TTS_PROVIDER != "mimo":
        return Response(content=b"", media_type="audio/wav")
    from services.tts_service import get_tts_service
    tts = get_tts_service()
    return StreamingResponse(
        tts.synthesize_stream(req.text),
        media_type="audio/wav",
        headers={"Content-Disposition": "inline"}
    )


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    history = session_service.get_history(session_id)
    messages = [Message(**m) for m in history]
    return HistoryResponse(session_id=session_id, history=messages)