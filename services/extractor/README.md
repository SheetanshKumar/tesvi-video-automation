# extractor

Turns raw source content into validated MCQs via Claude Sonnet 5. See
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §3.3.

**Responsibilities**
- Consume `source.ingested` Pub/Sub messages.
- Load raw text from GCS.
- Call Claude Sonnet 5 with a cached system prompt + tool-use structured
  output schema. Second critique pass scores each question 0.00–1.00.
- Write `question_sets` + `questions` rows to Postgres.
- Publish `questions.extracted`.
- Enforce per-source and per-day USD budget caps.

**Runtime**: Cloud Run Service, Python 3.11.

**Design rule** — must remain delivery-mode-agnostic: no YouTube /
video / test-env shape leaks into the extraction prompt or output
schema. See [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §3.3.

## Endpoints (scaffold)

| Method | Path       | Purpose      |
|--------|------------|--------------|
| GET    | `/healthz` | Liveness     |
| GET    | `/readyz`  | Readiness    |

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
uvicorn extractor.main:app --reload
```

Run tests:

```bash
pytest
```
