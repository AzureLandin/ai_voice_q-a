import io
import requests
from pydub import AudioSegment
from config import SILICONFLOW_API_KEY, SILICONFLOW_ASR_MODEL


class ASRService:
    API_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"

    def __init__(self):
        self._api_key = SILICONFLOW_API_KEY
        self._model = SILICONFLOW_ASR_MODEL

    def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""

        print(f"[ASR] Received {len(audio_bytes)} bytes")

        # 转换音频为 WAV 16kHz mono
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            print(f"[ASR] Audio: {audio.frame_rate}Hz, {audio.channels}ch, {audio.duration_seconds}s")
            audio = audio.set_frame_rate(16000).set_channels(1)
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            wav_bytes = wav_buffer.getvalue()
            print(f"[ASR] Converted to WAV: {len(wav_bytes)} bytes")
        except Exception as e:
            print(f"[ASR] Audio conversion error: {e}")
            wav_bytes = audio_bytes

        headers = {
            "Authorization": f"Bearer {self._api_key}",
        }
        files = {
            "file": ("audio.wav", io.BytesIO(wav_bytes), "audio/wav"),
            "model": (None, self._model),
        }
        resp = requests.post(self.API_URL, headers=headers, files=files, timeout=30)
        
        if resp.status_code != 200:
            print(f"[ASR] Error {resp.status_code}: {resp.text}")
        
        resp.raise_for_status()
        result = resp.json().get("text", "").strip()
        print(f"[ASR] Result: {result}")
        return result


_asr_instance = None


def get_asr_service():
    global _asr_instance
    if _asr_instance is None:
        _asr_instance = ASRService()
    return _asr_instance