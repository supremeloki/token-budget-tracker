# token-budget-tracker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Token budget accounting for LLM apps: split a context window into category budgets (system / context / response), spend with hard exhaustion errors, refund on aborts, and project how many calls you can afford.

## 🚀 Overview

Agents blow their token budget mid-conversation and crash at the worst moment. `token-budget-tracker` makes the budget explicit up front: the total limit splits into named categories by share (default 15/55/30), every spend is a recorded `UsageRecord`, exceeding a category raises `BudgetExhaustedError` *before* the call — not after. Aborted generations get refunded, and `projection_at_rate` answers "how many more calls can I afford?"

## ✨ Features

- **Category budgets:** allocation shares validated to sum to 1.0
- **Spend by text or raw tokens:** strings estimated (~1.35 tokens/word), ints pass through
- **Hard exhaustion:** over-spend raises with requested vs remaining, never silently truncates
- **Refunds:** aborted/failed calls release their reserved tokens back to the category
- **Role tagging:** SYSTEM/USER/ASSISTANT/TOOL per record; tool overhead identifiable
- **Projection:** affordable call count at a given rate against remaining budget
- **Injectable clock:** deterministic record ordering in tests
- **Zero dependencies**

## 🚧 Structure

```
token-budget-tracker/
├── src/token_budget/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/token-budget-tracker.git
cd token-budget-tracker
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from token_budget import BudgetExhaustedError, Role, TokenBudgetTracker

tracker = TokenBudgetTracker(total_limit=8000)
tracker.spend("system", "You are a helpful assistant.", role=Role.SYSTEM)
tracker.spend("context", retrieved_document_text)

try:
    tracker.spend("response", 500)          # reserve for the answer
except BudgetExhaustedError as exc:
    print(exc)                              # requested X, only Y remain

print(tracker.report()["response"])
```

## 🔧 Error Handling

```text
BudgetError
├── BudgetExhaustedError    # spend exceeds the category's remaining capacity
├── UnknownCategoryError    # spend/refund on an unregistered category
└── invalid config          # limit < 1 or allocations not summing to 1.0
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen usage records
- Zero comments — names carry the meaning
- Exhaustion boundaries and refund symmetry asserted in tests

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi** - [kooroushmasoumi@gmail.com](mailto:kooroushmasoumi@gmail.com)

---

⭐ Star this repo if you find it useful!
