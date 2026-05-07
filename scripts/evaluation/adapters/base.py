"""Base adapter interface."""

from __future__ import annotations

from typing import Dict, List, Protocol


Message = Dict[str, object]


class ModelAdapter(Protocol):
    def generate(self, messages: List[Message]) -> str:
        """Generate a response from a conversation history."""

