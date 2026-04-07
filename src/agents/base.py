from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.state import WarRoomState


class BaseAgent(ABC):
    name: str = "base_agent"

    @abstractmethod
    def run(self, state: WarRoomState) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def clamp_confidence(value: float) -> float:
        return round(max(0.0, min(1.0, value)), 2)
