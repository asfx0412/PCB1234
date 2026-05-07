"""OpenAI-compatible chat completion adapter, suitable for vLLM."""

from __future__ import annotations

from typing import Dict, List, Optional

import requests


class OpenAICompatibleAdapter:
    def __init__(
        self,
        api_base: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 8192,
        timeout: int = 360,
        api_key: Optional[str] = None,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.api_key = api_key

    def generate(self, messages: List[Dict[str, object]]) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        response = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()

