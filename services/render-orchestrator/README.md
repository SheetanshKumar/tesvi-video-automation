# render-orchestrator

Validates render requests and submits Cloud Run Job executions for the
`renderer`. See
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §3.5.

**Responsibilities**
- Consume `questions.approved` (or handle HTTP render requests from
  `api`).
- Validate: template exists, question set is in a consumable state, no
  in-flight render for this (set, template, input-fingerprint) triple.
- Submit Cloud Run Job execution for [`renderer`](../renderer/README.md).
- Update `renders` row (`queued → rendering → succeeded/failed`).

**Runtime**: Cloud Run Service, Go 1.23. Never renders in-process — long
work belongs in the Job, not here.

## Endpoints (scaffold)

| Method | Path       | Purpose      |
|--------|------------|--------------|
| GET    | `/healthz` | Liveness     |
| GET    | `/readyz`  | Readiness    |

## Local run

```bash
cd services/render-orchestrator
go run ./cmd/render-orchestrator
```
