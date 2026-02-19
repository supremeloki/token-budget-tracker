import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from token_budget import (
    BudgetError,
    BudgetExhaustedError,
    Role,
    TokenBudgetTracker,
    UnknownCategoryError,
    UsageRecord,
    estimate_tokens,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        self.now += 1.0
        return self.now


def test_estimate_tokens_scales_words():
    assert estimate_tokens("one two three") == 4
    assert estimate_tokens("") == 0


def test_invalid_total_limit_rejected():
    with pytest.raises(BudgetError):
        TokenBudgetTracker(total_limit=0)


def test_allocations_must_sum_to_one():
    with pytest.raises(BudgetError):
        TokenBudgetTracker(total_limit=1000,
                           allocations={"a": 0.5, "b": 0.2})


def test_default_allocation_splits():
    tracker = TokenBudgetTracker(total_limit=1000)
    report = tracker.report()
    assert report["system"]["limit"] == 150
    assert report["context"]["limit"] == 550
    assert report["response"]["limit"] == 300


def test_spend_text_estimates_tokens():
    tracker = TokenBudgetTracker(total_limit=1000)
    record = tracker.spend("response", "word " * 10)
    assert record.tokens >= 13
    assert record.role is Role.USER


def test_spend_raw_int_tokens():
    tracker = TokenBudgetTracker(total_limit=1000)
    record = tracker.spend("context", 120)
    assert record.tokens == 120


def test_exhaustion_raises_with_details():
    tracker = TokenBudgetTracker(total_limit=200)
    with pytest.raises(BudgetExhaustedError):
        tracker.spend("response", 999)


def test_unknown_category_raises():
    tracker = TokenBudgetTracker(total_limit=100)
    with pytest.raises(UnknownCategoryError):
        tracker.spend("vibes", "text")


def test_refund_restores_capacity():
    tracker = TokenBudgetTracker(total_limit=300)
    record = tracker.spend("response", "some long text here for tokens")
    tracker.refund(record)
    report = tracker.report()
    assert report["response"]["spent"] == 0
    assert len(tracker.records) == 0


def test_refund_untracked_raises():
    tracker = TokenBudgetTracker(total_limit=100)
    ghost = UsageRecord(category="response", role=Role.USER,
                        tokens=5, recorded_at=1.0)
    with pytest.raises(BudgetError):
        tracker.refund(ghost)


def test_report_utilization_grows():
    tracker = TokenBudgetTracker(total_limit=400)
    tracker.spend("system", 40)
    report = tracker.report()
