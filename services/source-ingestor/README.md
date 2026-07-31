# source-ingestor

Fetches and normalizes raw content from every supported source type,
writes it to GCS, and publishes `source.ingested`. See
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §3.2.

**Responsibilities**
- One codebase, polymorphic `SourceAdapter` per type:
  `TextAdapter`, `ArticleUrlAdapter`, `RssAdapter`, `WebsiteAdapter`,
  `PdfAdapter`.
- `robots.txt` compliance, domain allow-list, fetch timeouts + circuit
  breakers.
- Content dedup via SHA-256 on normalized text (per-owner or global; see
  [`db/migrations/0002_sources.up.sql`](../../db/migrations/0002_sources.up.sql)).

**Runtime**: Cloud Run Service, Go 1.23.

## Endpoints (scaffold)

| Method | Path       | Purpose      |
|--------|------------|--------------|
| GET    | `/healthz` | Liveness     |
| GET    | `/readyz`  | Readiness    |

## Local run

```bash
cd services/source-ingestor
go run ./cmd/source-ingestor
```

Real adapters land as we implement Phase B in
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §15.
