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
                 allocations: dict[str, float] | None = None,
                 clock: Callable[[], float] | None = None) -> None:
        if total_limit < 1:
            raise BudgetError("total limit must be >= 1")
        self._clock = clock or time.time
        self._records: list[UsageRecord] = []
        shares = allocations or {"system": 0.15, "context": 0.55, "response": 0.30}
        if abs(sum(shares.values()) - 1.0) > 0.001:
            raise BudgetError("allocations must sum to 1.0")
        self._categories = {
            name: CategoryBudget(name=name, limit=round(share * total_limit))
            for name, share in shares.items()
        }

    @property
    def total_limit(self) -> int:
        return sum(category.limit for category in self._categories.values())

    @property
    def records(self) -> tuple[UsageRecord, ...]:
        return tuple(self._records)

    def spend(self, category: str, text: str | int, *,
              role: Role = Role.USER) -> UsageRecord:
        if category not in self._categories:
            raise UnknownCategoryError(category)
        tokens = text if isinstance(text, int) else estimate_tokens(text)
        budget = self._categories[category]
        if tokens > budget.remaining:
            raise BudgetExhaustedError(tokens, budget.remaining)
        budget.spent += tokens
        record = UsageRecord(
            category=category,
            role=role,
            tokens=tokens,
            recorded_at=self._clock(),
        )
        self._records.append(record)
        return record

    def refund(self, record: UsageRecord) -> None:
        if record not in self._records:
            raise BudgetError("refund of untracked record")
        self._categories[record.category].spent -= record.tokens
        self._records.remove(record)

    def report(self) -> dict[str, dict[str, float]]:
        return {
            name: {
                "limit": category.limit,
                "spent": category.spent,
                "remaining": category.remaining,
                "utilization": category.utilization,
            }
            for name, category in self._categories.items()
        }

    def can_afford(self, category: str, tokens: int) -> bool:
        budget = self._categories.get(category)
        if budget is None:
            return False
        return tokens <= budget.remaining

    def projection_at_rate(self, tokens_per_call: int,
                           calls_planned: int, category: str = "response") -> int:
        budget = self._categories[category]
        affordable = min(calls_planned, budget.remaining // tokens_per_call)
        return affordable * tokens_per_call
