import uuid
from datetime import datetime
from typing import List, Dict, Optional
from config import MAX_HISTORY_TURNS


class SessionService:
    def __init__(self, max_turns: int = MAX_HISTORY_TURNS):
        self._sessions: Dict[str, List[Dict]] = {}
        self._max_turns = max_turns

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        return session_id

    def get_or_create(self, session_id: Optional[str]) -> str:
        if session_id and session_id in self._sessions:
            return session_id
        return self.create_session()

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
        max_messages = self._max_turns * 2
        if len(self._sessions[session_id]) > max_messages:
            self._sessions[session_id] = self._sessions[session_id][-max_messages:]

    def get_history(self, session_id: str) -> List[Dict]:
        return self._sessions.get(session_id, [])

    def get_context(self, session_id: str) -> List[Dict]:
        """Return messages suitable for AI API (role + content only)."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self.get_history(session_id)
        ]


# Global singleton
session_service = SessionService()
