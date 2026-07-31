# reviewer-ui

Human-in-the-loop review UI for LLM-extracted questions. See
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §3.4.

**Responsibilities**
- Humans approve / reject / edit questions before public delivery
  (YouTube, public test packs).
- Flips `question_sets.publish_status` between
  `unreviewed → approved / rejected`.
- **Not required for owner-private consumption** — a student running
  their own test session against their own extracted set doesn't need
  reviewer approval. See
  [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §18.4.
- Rejection reasons feed back into extraction prompts as future
  few-shot examples.

**Runtime**: Cloud Run Service, Next.js 15 (standalone), behind Google
Identity-Aware Proxy (IAP).

## Endpoints (scaffold)

- `GET /`         — home page
- `GET /healthz`  — liveness

## Local development

```bash
cd services/reviewer-ui
npm install
npm run dev            # http://localhost:3000
```

Type-check:

```bash
npm run typecheck
```

Real review workflow lands as we build Phase B in
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §15.
