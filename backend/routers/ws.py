import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from config import TTS_PROVIDER
from services.ai_service import ai_service
from services.session_service import session_service
from services.asr_service import get_asr_service

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)


def _tts_worker(tts, text, queue):
    try:
        has_data = False
        for chunk in tts.synthesize_stream(text):
            if chunk:
                has_data = True
                queue.put(chunk)
        queue.put(("success", None) if has_data else ("fallback", None))
    except Exception as e:
        print(f"[TTS Worker Error] {e}")
        queue.put(("fallback", None))


@router.websocket("/ws/audio/{session_id}")
async def audio_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    sid = session_service.get_or_create(session_id)
    asr = get_asr_service()
    tts = None
    if TTS_PROVIDER == "mimo":
        from services.tts_service import get_tts_service
        tts = get_tts_service()
    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            text = asr.transcribe(audio_bytes)
            if not text:
                await websocket.send_text(json.dumps({"type": "error", "error": "无法识别语音，请重试"}))
                continue
            session_service.add_message(sid, "user", text)
            context = session_service.get_context(sid)

            await websocket.send_text(json.dumps({
                "type": "text_start",
                "user_text": text,
                "tts_provider": TTS_PROVIDER,
            }))

            full_answer = ""
            for delta in ai_service.ask_stream(context):
                full_answer += delta
                await websocket.send_text(json.dumps({
                    "type": "text_delta",
                    "text": delta,
                }))

            await websocket.send_text(json.dumps({"type": "text_end"}))
            session_service.add_message(sid, "assistant", full_answer)

            if tts:
                try:
                    queue = Queue()
                    loop = asyncio.get_event_loop()
                    loop.run_in_executor(executor, _tts_worker, tts, full_answer, queue)
                    
                    has_audio = False
                    while True:
                        result = await loop.run_in_executor(None, queue.get)
                        if isinstance(result, tuple):
                            status, _ = result
                            if status == "fallback":
                                print("[TTS] Fallback to WebSpeech")
                                await websocket.send_text(json.dumps({
                                    "type": "tts_fallback",
                                    "text": full_answer
                                }))
                            break
                        else:
                            chunk = result
                            if chunk is None:
                                break
                            has_audio = True
                            await websocket.send_bytes(chunk)
                    
                    if has_audio:
                        await websocket.send_text(json.dumps({"type": "audio_end"}))
                except Exception as e:
                    print(f"TTS error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "tts_fallback",
                        "text": full_answer
                    }))

    except WebSocketDisconnect:
        pass
