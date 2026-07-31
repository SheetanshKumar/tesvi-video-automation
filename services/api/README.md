# api

Control-plane HTTP API for TesVi. See
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §3.1.

**Responsibilities**
- CRUD on `sources`, `question_sets`, `questions`, `video_templates`,
  `renders`, `publications`.
- Publish commands to Pub/Sub (`questions.approved`,
  `render.requested`, ...).
- Does *not* call the LLM, does *not* render, does *not* upload — pure
  command/query surface.

**Runtime**: Cloud Run Service, Go 1.23.

## Endpoints (scaffold)

| Method | Path       | Purpose                           |
|--------|------------|-----------------------------------|
| GET    | `/healthz` | Liveness                          |
| GET    | `/readyz`  | Readiness (will grow dependencies)|

## Local run

```bash
cd services/api
go run ./cmd/api
# → :8080
```

Real handlers land per-domain as the phases in
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §15 progress.
