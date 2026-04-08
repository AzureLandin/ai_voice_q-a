from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.chat import router as chat_router
from routers.ws import router as ws_router
from config import FRONTEND_ORIGIN

app = FastAPI(title="AI语音问答", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
