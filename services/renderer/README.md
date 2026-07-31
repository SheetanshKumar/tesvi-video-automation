# renderer

The one **Cloud Run Job**, not a Service — long-running (minutes) CPU
work with no attached HTTP request. See
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §3.6.

**Responsibilities**
- Load a `renders` row by `RENDER_ID`.
- Synthesize TTS narration (Google Cloud TTS Neural2 / Chirp3).
- Render frames via **Remotion** per the template spec
  (see [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §7.2).
- Mux audio + video with `ffmpeg`; generate a thumbnail.
- Upload mp4 + thumbnail + captions to GCS.
- Update the `renders` row; publish `render.completed`.
- Idempotent: on retry, if `renders.status = 'succeeded'`, exit 0
  without work.

**Why a Job, not a Service** — Cloud Run Services cap requests at 60
minutes; Jobs go to 24h and are designed for batch. Renders that need
more than the request timeout would silently die in a Service.

**Runtime**: Cloud Run Job, Node 22, TypeScript.

## Invocation

```bash
RENDER_ID=<uuid> node dist/index.js
```

## Local development

```bash
cd services/renderer
npm install
npm run dev            # tsx watch (fast iteration)
npm run typecheck
npm run build && npm start
```

Remotion / TTS / ffmpeg / GCS wiring lands as we implement Phase C in
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) §15.
