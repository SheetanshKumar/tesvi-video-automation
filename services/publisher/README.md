# publisher

Uploads rendered videos to YouTube (and later Instagram Reels / TikTok /
YouTube Shorts). See
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §3.7.

**Responsibilities**
- Consume `render.completed` (or accept manual triggers from `api`).
- YouTube OAuth token refresh (refresh token from Secret Manager).
- Upload mp4 + thumbnail + captions with metadata; set visibility
  (`private` by default; humans flip to `public`).
- Quota-aware throttling — YouTube Data API defaults to ~6 uploads/day
  per project (1600 units × 10 000 daily quota); see §14.
- Idempotency via `idempotency_keys` (scope `youtube_upload`,
  key = `render_id`).

**Runtime**: Cloud Run Service, Go 1.23.

## Endpoints (scaffold)

| Method | Path       | Purpose      |
|--------|------------|--------------|
| GET    | `/healthz` | Liveness     |
| GET    | `/readyz`  | Readiness    |

## Local run

```bash
cd services/publisher
go run ./cmd/publisher
```
