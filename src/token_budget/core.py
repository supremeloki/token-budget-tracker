from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Sequence


class BudgetError(Exception):
    pass


class BudgetExhaustedError(BudgetError):
    def __init__(self, requested: int, remaining: int) -> None:
        super().__init__(f"requested {requested} tokens, only {remaining} remain")


class UnknownCategoryError(BudgetError):
    def __init__(self, category: str) -> None:
        super().__init__(f"unknown budget category: {category!r}")


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
