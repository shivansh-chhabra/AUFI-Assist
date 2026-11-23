"""Minimal Ollama client (HTTP API, standard library only). Ported from your friend's agent.py."""
import json
import re
import time
import urllib.request
from typing import Optional

from .. import config


class Ollama:
    def __init__(self, url=None, model=None, num_ctx=None, temperature=0.0, timeout=None):
        self.url = (url or config.LLM_URL).rstrip("/")
        self.model = model or config.LLM_MODEL
        self.num_ctx = num_ctx or config.LLM_NUM_CTX
        self.temperature = temperature
        self.timeout = timeout or config.LLM_TIMEOUT
        # never route localhost through a corporate/system proxy
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self._checked_at = 0.0
        self._ok = False

    def _request(self, path, body=None, timeout=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.url + path, data=data, headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=timeout or self.timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    def available(self) -> bool:
        """True if Ollama is running and the model is installed (re-checked at most every 30 s)."""
        if time.time() - self._checked_at < 30:
            return self._ok
        self._checked_at = time.time()
        try:
            tags = self._request("/api/tags", timeout=3)
            names = [m.get("name", "") for m in tags.get("models", [])]
            self._ok = self.model in names or self.model + ":latest" in names
        except (OSError, ValueError):
            self._ok = False
        return self._ok

    def chat(self, messages: list[dict]) -> str:
        """One JSON-mode chat turn. Raises OSError/ValueError if Ollama is unreachable or misbehaves."""
        out = self._request("/api/chat", {
            "model": self.model, "messages": messages, "stream": False, "format": "json",
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx, "seed": 0}})
        return out.get("message", {}).get("content", "")


def parse_json(s: Optional[str]) -> Optional[dict]:
    s = (s or "").strip()
    try:
        obj = json.loads(s)
    except ValueError:
        m = re.search(r"\{.*\}", s, re.S)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
        except ValueError:
            return None
    return obj if isinstance(obj, dict) else None
