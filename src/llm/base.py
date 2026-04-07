from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    @abstractmethod
    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_model: type[T],
    ) -> T:
        raise NotImplementedError
