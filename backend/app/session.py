"""In-memory case sessions. Nothing is written to disk: a patient's answers vanish when the
server restarts or the session expires, which is deliberate for a shared hospital machine."""
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from . import config


@dataclass
class Session:
    id: str
    created: float = field(default_factory=time.time)
    touched: float = field(default_factory=time.time)
    lock: threading.RLock = field(default_factory=threading.RLock)

    started: bool = False
    initial_text: str = ""
    scorer_state: Any = None            # opaque, owned by scoring/scorer.py
    asked: list[dict] = field(default_factory=list)   # {feature, text, answer}
    pending: Optional[dict] = None      # the question currently waiting for an answer
    posterior: dict[str, float] = field(default_factory=dict)
    previous: dict[str, float] = field(default_factory=dict)

    finished: bool = False
    stop_reason: Optional[str] = None
    shortlist: list[str] = field(default_factory=list)
    explanation: Optional[list[dict]] = None   # wire-format dicts
    evidence: Optional[dict] = None
    messages: list[dict] = field(default_factory=list)

    def add_message(self, role: str, text: str, **extra: Any) -> None:
        self.messages.append({"id": f"h-{self.id}-{len(self.messages)}", "role": role, "text": text, **extra})


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def get(self, cid: Optional[str]) -> Session:
        cid = cid or f"anon-{uuid.uuid4().hex[:8]}"
        with self._lock:
            self._prune()
            s = self._sessions.get(cid)
            if s is None:
                s = self._sessions[cid] = Session(id=cid)
            s.touched = time.time()
            return s

    def peek(self, cid: str) -> Optional[Session]:
        with self._lock:
            return self._sessions.get(cid)

    def delete(self, cid: str) -> None:
        with self._lock:
            self._sessions.pop(cid, None)

    def _prune(self) -> None:
        cutoff = time.time() - config.SESSION_TTL_HOURS * 3600
        for k in [k for k, v in self._sessions.items() if v.touched < cutoff]:
            del self._sessions[k]


store = SessionStore()
