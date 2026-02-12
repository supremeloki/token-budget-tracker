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
    words = len(text.split())
    return max(1, round(words * 1.35))


@dataclass(frozen=True)
class UsageRecord:
    category: str
    role: Role
    tokens: int
    recorded_at: float

    @property
    def is_overhead(self) -> bool:
        return self.role is Role.TOOL


@dataclass
class CategoryBudget:
    name: str
    limit: int
    spent: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.spent)

    @property
    def utilization(self) -> float:
        if self.limit == 0:
            return 0.0
        return round(self.spent / self.limit, 4)


class TokenBudgetTracker:
    def __init__(self,
                 total_limit: int,
