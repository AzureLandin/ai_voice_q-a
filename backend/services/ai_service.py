from typing import List, Dict, Generator
from config import OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL, SYSTEM_PROMPT


class AIService:
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE,
        )
        self._model = OPENAI_MODEL

    def ask(self, messages: List[Dict]) -> str:
        try:
            full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            response = self._client.chat.completions.create(
                model=self._model,
                messages=full_messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"AI API error: {e}")
            return "抱歉，我暂时无法回答，请稍后再试。"

    def ask_stream(self, messages: List[Dict]) -> Generator[str, None, None]:
        try:
            full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            response = self._client.chat.completions.create(
                model=self._model,
                messages=full_messages,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"AI API stream error: {e}")
            yield "抱歉，我暂时无法回答，请稍后再试。"


ai_service = AIService()
