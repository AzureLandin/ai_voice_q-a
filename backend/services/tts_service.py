import base64
import json
import struct
import requests
import time
from config import MIMO_API_KEY, MIMO_TTS_MODEL, MIMO_VOICE, MIMO_AUDIO_FORMAT


class TTSService:
    API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
    SAMPLE_RATE = 24000
    NUM_CHANNELS = 1
    BITS_PER_SAMPLE = 16

    def __init__(self):
        self._api_key = MIMO_API_KEY
        self._model = MIMO_TTS_MODEL
        self._voice = MIMO_VOICE
        self._format = MIMO_AUDIO_FORMAT

    def _make_wav_header(self, data_size=0):
        byte_rate = self.SAMPLE_RATE * self.NUM_CHANNELS * self.BITS_PER_SAMPLE // 8
        block_align = self.NUM_CHANNELS * self.BITS_PER_SAMPLE // 8
        file_size = 36 + data_size

        header = bytearray()
        header.extend(b'RIFF')
        header.extend(struct.pack('<I', file_size))
        header.extend(b'WAVE')
        header.extend(b'fmt ')
        header.extend(struct.pack('<I', 16))
        header.extend(struct.pack('<HH', 1, self.NUM_CHANNELS))
        header.extend(struct.pack('<I', self.SAMPLE_RATE))
        header.extend(struct.pack('<I', byte_rate))
        header.extend(struct.pack('<HH', block_align, self.BITS_PER_SAMPLE))
        header.extend(b'data')
        header.extend(struct.pack('<I', data_size))
        return bytes(header)

    def synthesize(self, text: str) -> bytes:
        if not text.strip():
            return b""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "api-key": self._api_key,
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "user", "content": ""},
                {"role": "assistant", "content": text},
            ],
            "audio": {
                "format": self._format,
                "voice": self._voice,
            },
        }

        resp = requests.post(self.API_URL, headers=headers, json=payload, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        audio_b64 = data["choices"][0]["message"]["audio"]["data"]
        pcm_data = base64.b64decode(audio_b64)
        return self._make_wav_header(len(pcm_data)) + pcm_data

    def _synthesize_stream_internal(self, text: str, skip_header: bool = False, attempt: int = 1):
        if not text.strip():
            yield b""
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "api-key": self._api_key,
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "user", "content": ""},
                {"role": "assistant", "content": text},
            ],
            "audio": {
                "format": "pcm16",
                "voice": self._voice,
            },
            "stream": True,
        }

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=5,
            stream=True
        )
        response.raise_for_status()

        first_chunk = True

        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    audio = delta.get("audio")
                    if audio is None:
                        continue
                    audio_b64 = audio.get("data")
                    if audio_b64:
                        pcm_chunk = base64.b64decode(audio_b64)

                        if first_chunk and not skip_header:
                            first_chunk = False
                            wav_header = self._make_wav_header(0)
                            yield wav_header + pcm_chunk
                        else:
                            first_chunk = False
                            yield pcm_chunk
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    def synthesize_stream(self, text: str, skip_header: bool = False, max_retries: int = 1):
        if not text.strip():
            yield b""
            return

        for attempt in range(1, max_retries + 1):
            try:
                print(f"[TTS] Attempt {attempt}/{max_retries} for text: '{text[:30]}...'")
                
                has_data = False
                for chunk in self._synthesize_stream_internal(text, skip_header, attempt):
                    if chunk:
                        has_data = True
                        yield chunk
                
                if has_data:
                    print(f"[TTS] Attempt {attempt} succeeded")
                    return
                else:
                    print(f"[TTS] Attempt {attempt} returned no data, retrying...")
                    if attempt < max_retries:
                        time.sleep(0.5)
                        
            except requests.exceptions.Timeout:
                print(f"[TTS] Attempt {attempt} timed out, retrying...")
                if attempt < max_retries:
                    time.sleep(1)
            except Exception as e:
                print(f"[TTS] Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(0.5)
        
        print(f"[TTS] All {max_retries} attempts failed, giving up")
        yield b""


_tts_instance = None


def get_tts_service():
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TTSService()
    return _tts_instance
