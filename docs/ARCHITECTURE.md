# TesVi v2 — Cloud-Native Architecture Design

> Status: **Proposal / RFC**
> Owner: TBD
> Last updated: 2026-08-01

This document describes the target architecture for evolving TesVi from a
single-machine Python script into a cloud-native service that:

1. Ingests content from multiple **source types** (raw text, article URLs, RSS
   feeds, whole websites).
2. Uses an LLM to **extract validated MCQs** with topic/difficulty/exam
   metadata and explanations.
3. Persists questions in a queryable database.
4. Renders MCQ videos on demand from stored question sets using versioned
   templates.
5. Publishes videos to YouTube (and later other platforms).

Everything runs on Google Cloud, mostly on Cloud Run and Cloud Run Jobs, with
Cloud SQL Postgres as the system of record.

---

## 1. Goals & non-goals

### Goals

- **Source-agnostic ingestion**: adding a new source type (e.g. a PDF) is a
  new adapter class, not a pipeline rewrite.
- **Deterministic, reproducible rendering**: same inputs + same template
  version → byte-identical output. Enables golden-file testing and safe
  re-renders.
- **Independent rendering**: renders trigger from `question_set` events, not
  from source ingestion. A question set can be re-rendered against a new
  template without re-extraction.
- **Human-in-the-loop review** before any public YouTube upload.
- **Cost-scaled-to-zero** for idle workloads via Cloud Run.
- **Idempotent, retry-safe pipeline** — every stage can be re-run without
  side-effect duplication.

### Non-goals (for v2)

- Real-time / live rendering.
- Interactive quiz UX (this is a video generator, not a quiz app).
- Multi-tenant SaaS (single-org for now; multi-tenancy is a v3 concern).
- Mobile apps.

---

## 2. High-level architecture

```
                    ┌────────────────────────────────────────────┐
                    │            Control Plane (API)             │
                    │        Cloud Run service · REST/gRPC       │
                    └───────┬──────────────────────────────┬─────┘
                            │                              │
              submit source │                              │ trigger render
                            ▼                              ▼
        ┌──────────────────────────────┐        ┌──────────────────────┐
        │  source.ingestor             │        │  render.orchestrator │
        │  Cloud Run service (per type)│        │  Cloud Run service   │
        │  · text                      │        └──────────┬───────────┘
        │  · article-url (readability) │                   │
        │  · rss                        │                   │
        │  · website (crawl+parse)     │                   │
        └────────────┬─────────────────┘                   │
                     │ writes raw snapshot                 │
                     ▼                                      │
             ┌──────────────┐                              │
             │  GCS: sources│                              │
             └──────┬───────┘                              │
                    │ publishes                            │
                    ▼                                      ▼
          ┌─────────────────────┐            ┌──────────────────────────┐
          │  Pub/Sub:           │            │  Pub/Sub: render.requested│
          │  source.ingested    │            └──────────────┬───────────┘
          └─────────┬───────────┘                           │
                    ▼                                        ▼
        ┌────────────────────────┐                ┌──────────────────────┐
        │  extraction.worker     │                │  renderer            │
        │  Cloud Run service     │                │  Cloud Run Job       │
        │  · Claude Sonnet 5 API │                │  · Remotion / MoviePy│
        │  · structured output   │                │  · TTS synth         │
        │  · self-critique pass  │                │  · ffmpeg mux        │
        └────────┬───────────────┘                └───────┬──────────────┘
                 │ writes questions                       │ writes mp4+thumb
                 ▼                                        ▼
       ┌──────────────────────┐                  ┌──────────────────┐
       │  Cloud SQL Postgres  │◄─────────────────│  GCS: rendered   │
       │  (system of record)  │                  └────────┬─────────┘
       └────────┬─────────────┘                           │ publishes
                │ notifies                                ▼
                ▼                                ┌──────────────────────┐
       ┌──────────────────────┐                 │  Pub/Sub:            │
       │  Reviewer UI         │                 │  render.completed    │
       │  Cloud Run service   │                 └────────┬─────────────┘
       │  (Next.js + IAP)     │                          │
       └──────────────────────┘                          ▼
                                              ┌────────────────────────┐
                                              │  publisher             │
                                              │  Cloud Run service     │
                                              │  · YouTube Data API v3 │
                                              │  · quota-aware queue   │
                                              └────────────────────────┘
```

**Message bus**: Cloud Pub/Sub for all cross-service events. Every downstream
handler is idempotent (keyed off entity IDs, not message IDs).

**Sync path**: Control-plane API writes are synchronous; everything else is
event-driven.

---

## 3. Services

Each service is a separately deployable Cloud Run unit. All share a common
Python (or TypeScript) base image with structured logging and OTel tracing
preconfigured.

### 3.1 Control Plane API (`api`)

- **Runtime**: Cloud Run service, min instances 1 (for latency), max 10.
- **Language**: Python (FastAPI) or TypeScript (Nest/Fastify).
- **Responsibilities**:
  - CRUD on sources, question sets, questions, templates, renders,
    publications.
  - Enqueue commands by publishing to Pub/Sub (does not do work inline).
  - Auth via Google Identity-Aware Proxy (IAP) for the reviewer/admin UI;
    service-to-service via GCP service accounts + OIDC.
- **Anti-goal**: does *not* call the LLM, does *not* render, does *not*
  upload to YouTube. Pure command/query surface.

### 3.2 Source Ingestor (`source-ingestor`)

- **Runtime**: Cloud Run service, scale-to-zero.
- **One codebase, multiple adapters** — polymorphism over `SourceAdapter`:

  ```
  SourceAdapter
    ├─ TextAdapter          # already-normalized text, no fetch needed
    ├─ ArticleUrlAdapter    # trafilatura / readability-lxml for clean extraction
    ├─ RssAdapter           # feedparser; yields ArticleUrl subjobs
    ├─ WebsiteAdapter       # bounded crawler (respects robots.txt, depth-limited)
    └─ PdfAdapter           # pypdfium2 for text PDFs; Document AI for scans (§18)
  ```
- **Output**: writes a `raw_content` blob to `gs://tesvi-sources/<hash>.txt`
  and a `sources` row with `content_hash` (SHA-256 of normalized text) for
  dedup. Publishes `source.ingested` with the source ID.
- **Guardrails**:
  - `robots.txt` compliance (`urllib.robotparser`).
  - Domain allow-list configured in Secret Manager — no arbitrary URL fetch.
  - Fetch timeouts + circuit breaker per domain.
  - HTML → text via `trafilatura` (much better than BS4 for article extraction).

> **Design rule — delivery-mode-agnostic**: the extractor MUST NOT know
> about YouTube, video templates, or any specific delivery surface. Its
> job ends when validated questions are in the DB. This is what lets a
> future test-runner, flashcard generator, or podcast synthesizer
> (see §18) plug in without touching extraction. Anything YouTube-shaped
> (SEO tags, thumbnail hints, description templates) belongs in the
> video-render or publisher layer, never in the extraction prompt.

### 3.3 Extraction Worker (`extractor`)

- **Runtime**: Cloud Run service, concurrency=1 per instance (LLM calls are
  long-running), max instances tunable per cost budget.
- **Trigger**: Pub/Sub push subscription on `source.ingested`.
- **Flow**:
  1. Load source text from GCS.
  2. Chunk if needed (target ≤ 8k tokens per call for latency; source-aware
     chunking, not naive splits).
  3. Call **Claude Sonnet 5** (`claude-sonnet-5`) with:
     - A cached system prompt (question rubric, difficulty definitions,
       exam taxonomy, output schema) — use **prompt caching** on the
     fixed prefix; the chunk is the only per-call variable content.
     - A **tool schema** that forces structured JSON output for questions
       (client-side validation via `pydantic`). Tool use is more reliable
       than free-form JSON.
  4. **Self-critique pass**: second Claude call that scores each question
     0.0–1.0 on ambiguity, factual grounding to source, and difficulty
     accuracy. Questions below a threshold get flagged (not silently
     dropped) for reviewer attention.
  5. Write `question_sets` + `questions` rows; publish `questions.extracted`.
- **Cost accounting**: record `extraction_cost_usd` per set from token
  counts. Enforce a per-source and per-day budget cap in Secret Manager.

### 3.4 Reviewer UI (`reviewer-ui`)

- **Runtime**: Cloud Run service behind IAP.
- **Frontend**: Next.js.
- **Function**: humans flip `question_sets.publish_status` to
  `approved`/`rejected` and edit individual questions before public
  delivery. Rejection reasons feed back into extraction prompts as future
  few-shot examples (a small feedback loop).
- **Scope**: gates *public* delivery (YouTube, public test packs) only.
  An owner consuming their own extracted set on a private surface
  (personal test session) does not require reviewer approval —
  `extraction_status = 'extracted'` is enough. See §18.
- **Why mandatory before public v1 GA**: mitigates hallucination *and*
  YouTube spam-flag risk (see §14).

### 3.5 Render Orchestrator (`render-orchestrator`)

- **Runtime**: Cloud Run service.
- **Trigger**: HTTP (from API) or Pub/Sub on `questions.approved`.
- **Function**: validates a render request (question set is approved,
  template exists, no active render for this pair), then submits a
  **Cloud Run Job execution** for the renderer and records a `renders` row
  as `queued → rendering`.

### 3.6 Renderer (`renderer`)

- **Runtime**: **Cloud Run Job**, not a service. Long-running (minutes to
  ~hour), CPU-bound, no HTTP request tied to it.
- **Why Job, not Service**: Cloud Run services have a 60-minute request
  timeout; Cloud Run Jobs support up to 24h and are designed for batch. This
  is the single most common architectural mistake in this pattern.
- **Resources**: 4–8 vCPU, 8–16 GB memory, no GPU (Cloud Run Jobs don't
  offer GPU; CPU is fine for the rendering tech below).
- **Flow**:
  1. Pull question set + template from Postgres.
  2. Synthesize TTS audio per line (Google Cloud TTS Neural2 or Chirp3 —
     **not** gTTS; enterprise voice quality matters).
  3. Render frames per the template spec.
  4. Mux audio+video with `ffmpeg`.
  5. Generate a thumbnail (a specific frame or a separate template render).
  6. Upload mp4 + thumb + captions to GCS.
  7. Update `renders` row and publish `render.completed`.
- **Idempotency**: render job execution keyed by `render_id`; on retry, if
  `renders.status = 'succeeded'`, exit 0 without work.

### 3.7 Publisher (`publisher`)

- **Runtime**: Cloud Run service.
- **Trigger**: Pub/Sub on `render.completed` OR manual via API.
- **Function**:
  - Handles YouTube OAuth token refresh (refresh token in Secret Manager).
  - Uploads mp4, sets title/description/tags/thumbnail/visibility.
  - Enforces quota-aware throttling (see §14: **1600 units per upload**,
    default 10,000 units/day/project ⇒ ~6 uploads/day; needs quota bump
    for anything beyond).
  - Records `publications` row with YouTube video ID.
  - Idempotency via `idempotency_keys` table (scope `youtube_upload`,
    key = `render_id`) to prevent double-upload on retry.

### 3.8 Scheduler / Cron

- **Cloud Scheduler** jobs:
  - RSS feed poller (every N minutes per feed, respecting `ETag`/`Last-Modified`).
  - Retry sweeper (find stuck jobs older than X and re-enqueue).
  - Cost/quota rollup for daily reports.

---

## 4. Data model (Cloud SQL Postgres)

Schema is designed for query flexibility (topic/difficulty/exam filters),
provenance (every question links back to its source), and reproducibility
(templates and renders are versioned).

```sql
create extension if not exists pgcrypto;

-- 4.1 Sources: raw inputs
create table sources (
  id                  uuid primary key default gen_random_uuid(),
  type                text not null check (type in ('text','article_url','rss_item','website','pdf','user_upload')),
  uri                 text,                            -- URL if applicable
  raw_content_gcs_uri text not null,                   -- gs://tesvi-sources/<sha>.txt
  content_hash        text not null,                   -- sha256 of normalized text
  title               text,
  author              text,
  published_at        timestamptz,
  ingested_at         timestamptz not null default now(),
  ingest_status       text not null default 'pending'
                          check (ingest_status in ('pending','fetched','failed','skipped')),
  ingest_error        text,
  -- Multi-tenancy (see §18: multi-modal delivery). owner_id is null for
  -- system-ingested sources (RSS crawlers, admin uploads); populated for
  -- user-uploaded PDFs etc.
  owner_id            uuid,                            -- FK users(id) when users table exists
  visibility          text not null default 'private'
                          check (visibility in ('private','org','public')),
  metadata            jsonb not null default '{}'::jsonb,
  -- Content dedup is scoped to owner: two users uploading the same PDF
  -- each get their own row, but one user re-uploading dedups.
  unique (owner_id, content_hash)
);
create index on sources (type, ingested_at desc);
create index on sources (owner_id) where owner_id is not null;

-- 4.2 Question sets: a batch generated from one source
--
-- Two independent status axes (see §18):
--   extraction_status  — pipeline state (did the LLM run successfully?)
--   publish_status     — public-consumption gate (has a human approved
--                        this set for YouTube / any public delivery?)
--
-- An owner can always consume their own extracted set in private modes
-- (test-env, personal review). publish_status only gates public surfaces.
create table question_sets (
  id                  uuid primary key default gen_random_uuid(),
  source_id           uuid references sources(id) on delete set null,
  owner_id            uuid,                            -- FK users(id); null = system-owned
  visibility          text not null default 'private'
                          check (visibility in ('private','org','public')),
  title               text not null,
  topic               text not null,
  subtopic            text,
  language            text not null default 'en',
  extraction_status   text not null default 'pending'
                          check (extraction_status in
                                 ('pending','extracting','extracted','failed')),
  publish_status      text not null default 'unreviewed'
                          check (publish_status in
                                 ('unreviewed','approved','rejected')),
  extraction_model    text,                            -- 'claude-sonnet-5'
  extraction_cost_usd numeric(10,4),
  reviewed_by         text,
  reviewed_at         timestamptz,
  created_at          timestamptz not null default now(),
  metadata            jsonb not null default '{}'::jsonb
);
create index on question_sets (extraction_status);
create index on question_sets (publish_status);
create index on question_sets (topic);
create index on question_sets (owner_id) where owner_id is not null;

-- 4.3 Questions
create table questions (
  id                     uuid primary key default gen_random_uuid(),
  question_set_id        uuid not null references question_sets(id) on delete cascade,
  ordinal                int not null,
  question_text          text not null,
  options                jsonb not null,               -- {"A":"..","B":"..","C":"..","D":".."}
  correct_options        text[] not null,              -- ['A'] or ['A','C']
  multi_correct          boolean not null default false,
  explanation            text,
  difficulty             text not null
                            check (difficulty in ('easy','medium','hard','expert')),
  topics                 text[] not null default '{}',
  applicable_exams       text[] not null default '{}',  -- ['NEET','UPSC','SAT',...]
  bloom_level            text
                            check (bloom_level in
                                   ('remember','understand','apply','analyze','evaluate','create')),
  estimated_time_seconds int not null default 30,
  source_span            text,                          -- snippet the question is grounded in
  quality_score          numeric(3,2),                  -- 0.00–1.00
  status                 text not null default 'draft'
                            check (status in ('draft','approved','rejected')),
  rejection_reason       text,
  created_at             timestamptz not null default now(),
  metadata               jsonb not null default '{}'::jsonb,
  unique (question_set_id, ordinal)
);
create index on questions using gin (topics);
create index on questions using gin (applicable_exams);
create index on questions (difficulty);
create index on questions (status);

-- 4.4 Video templates (versioned; templates are data, not code)
create table video_templates (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  version      int not null,
  spec         jsonb not null,                          -- see §7 for DSL
  created_at   timestamptz not null default now(),
  created_by   text,
  unique (name, version)
);

-- 4.5 Renders
create table renders (
  id                 uuid primary key default gen_random_uuid(),
  question_set_id    uuid not null references question_sets(id),
  template_id        uuid not null references video_templates(id),
  status             text not null default 'queued'
                          check (status in
                                 ('queued','rendering','succeeded','failed','cancelled')),
  requested_at       timestamptz not null default now(),
  started_at         timestamptz,
  completed_at       timestamptz,
  video_gcs_uri      text,
  thumbnail_gcs_uri  text,
  captions_gcs_uri   text,
  duration_seconds   numeric(8,2),
  resolution         text,
  frame_rate         numeric(4,1),
  cost_usd           numeric(10,4),
  error              text,
  render_job_name    text,                              -- Cloud Run Job execution id
  input_fingerprint  text not null,                     -- sha256(questions+template+voice) → dedup renders
  metadata           jsonb not null default '{}'::jsonb,
  unique (question_set_id, template_id, input_fingerprint)
);
create index on renders (status, requested_at);

-- 4.6 Publications
create table publications (
  id           uuid primary key default gen_random_uuid(),
  render_id    uuid not null references renders(id),
  platform     text not null check (platform in ('youtube','instagram_reels','tiktok','shorts')),
  external_id  text,                                    -- YouTube video ID
  external_url text,
  title        text not null,
  description  text,
  tags         text[],
  visibility   text not null default 'private'
                    check (visibility in ('public','unlisted','private')),
  status       text not null default 'pending'
                    check (status in ('pending','uploading','uploaded','failed','removed')),
  uploaded_at  timestamptz,
  error        text,
  metadata     jsonb not null default '{}'::jsonb
);
create unique index on publications (render_id, platform)
  where status in ('uploading','uploaded');

-- 4.7 Idempotency keys (short-lived; expire after 7 days)
create table idempotency_keys (
  key         text primary key,
  scope       text not null,
  entity_id   uuid not null,
  created_at  timestamptz not null default now(),
  expires_at  timestamptz not null
);

-- 4.8 Audit log (append-only)
create table audit_events (
  id         bigserial primary key,
  actor      text not null,       -- 'system:extractor', 'user:sheetansh@…'
  action     text not null,       -- 'questions.approved'
  entity     text not null,       -- 'question_set'
  entity_id  uuid not null,
  payload    jsonb not null default '{}'::jsonb,
  at         timestamptz not null default now()
);
create index on audit_events (entity, entity_id, at desc);
```

**Migrations**: `alembic` (Python) or `sqlx migrate` (TS) — never
`create table` in app code.

**Connection pooling**: Cloud SQL Auth Proxy sidecar; `pgbouncer` if
connection count becomes an issue.

---

## 5. Storage layout (GCS)

Single bucket per env with logical prefixes; lifecycle rules on the raw
tiers to keep costs bounded.

```
gs://tesvi-<env>/
├── sources/<sha256>.txt                  # raw ingested content (immutable)
├── media-assets/
│   ├── avatars/{id}.png
│   ├── avatar-videos/{id}.mp4
│   ├── backgrounds/{id}.mp4
│   ├── fonts/{family}/{weight}.ttf
│   └── audio/misc/{name}.mp3             # bells, stingers
├── renders/{render_id}/
│   ├── video.mp4
│   ├── thumbnail.jpg
│   ├── captions.vtt
│   ├── narration.mp3
│   └── manifest.json                     # inputs + versions used
├── logs/renders/{render_id}/render.log
└── tmp/                                  # 7-day lifecycle delete
```

- **Sources**: `Nearline` after 30d, `Coldline` after 180d — cheap
  provenance.
- **Renders**: `Standard` for 90d, then `Nearline`. Never delete without
  operator action (they're the deliverable).
- **`manifest.json`** per render captures the exact inputs
  (`question_set_id`, `template_id`, `template_version`, voice, TTS model,
  ffmpeg version, git SHA) so renders are auditable and reproducible.

---

## 6. Event flow (Pub/Sub topics)

| Topic                  | Publisher              | Subscribers              | Payload                    |
|------------------------|------------------------|--------------------------|----------------------------|
| `source.ingested`      | source-ingestor        | extractor                | `{source_id}`              |
| `questions.extracted`  | extractor              | reviewer-ui notifier     | `{question_set_id}`        |
| `questions.approved`   | api (from reviewer)    | render-orchestrator      | `{question_set_id}`        |
| `render.requested`     | render-orchestrator    | (internal → Jobs API)    | `{render_id}`              |
| `render.completed`     | renderer               | publisher, notifier      | `{render_id, status}`      |
| `publication.completed`| publisher              | notifier                 | `{publication_id, status}` |
| `deadletter.*`         | Pub/Sub DLQ            | ops alerting             | (original + error)         |

All subscriptions are **push** (Cloud Run) with retry policy 7d and a
dead-letter topic. Every handler is idempotent on the entity ID.

---

## 7. Rendering deep-dive

### 7.1 Tech choice: Remotion vs. MoviePy/OpenCV

Two viable paths — pick before writing v2 render code:

| Aspect                 | **Remotion** (React) | **MoviePy + OpenCV** (Python) |
|------------------------|----------------------|-------------------------------|
| Language               | TS/React             | Python (matches rest of stack)|
| Animation primitives   | First-class (Framer-motion-esque, timing/easing built in) | Manual per-frame; barebones |
| Determinism            | Guaranteed           | Fragile (freetype, threading) |
| Preview / iteration    | Hot-reload in browser| Render + inspect              |
| Headless in Docker     | Native (Chromium)    | Native                        |
| Team ramp-up if all-Python | Higher           | Zero                          |
| Ceiling on visual polish   | High (real motion graphics) | Low without heavy custom code |

**Recommendation**: **Remotion** for anything meant for YouTube. The
production values gap between "OpenCV `putText`" and "Remotion motion
graphics" is the difference between "obviously automated" and "watchable".
The polyglot cost (one TS service in an otherwise Python stack) is worth it
here; the renderer's interface is `{ render_id }` in, `{ mp4_gcs_uri }` out —
language is invisible externally.

If you want to stay all-Python, **MoviePy** with proper compositing is the
next-best; retire OpenCV `cv2.putText` entirely.

### 7.2 Template as data (DSL)

Templates live in `video_templates.spec` as JSON and describe scenes,
transitions, and animation intent. The renderer interprets the spec — it
never hardcodes screen layouts.

```jsonc
{
  "resolution": [1920, 1080],
  "fps": 30,
  "voice": { "provider": "google_tts", "name": "en-US-Neural2-F" },
  "music": { "asset": "media-assets/audio/bg/lofi_01.mp3", "gain_db": -18 },
  "scenes": [
    {
      "type": "intro",
      "duration_s": 6,
      "props": { "title": "{{question_set.title}}",
                 "subtitle": "{{question_set.topic}}",
                 "avatar": "media-assets/avatar-videos/host_female.mp4" },
      "animations": [{ "target": "title", "in": "fade+rise", "duration_s": 0.6 }]
    },
    {
      "type": "question",
      "for_each": "questions",
      "duration_s": "{{item.estimated_time_seconds + 4}}",
      "props": {
        "question_text": "{{item.question_text}}",
        "options": "{{item.options}}",
        "timer_start": "{{item.estimated_time_seconds}}"
      },
      "animations": [
        { "target": "options.*", "in": "stagger_fade", "stagger_s": 0.15 },
        { "target": "timer", "type": "countdown" }
      ]
    },
    {
      "type": "answer_reveal",
      "for_each": "questions",
      "duration_s": 5,
      "props": { "correct": "{{item.correct_options}}", "explanation": "{{item.explanation}}" }
    },
    { "type": "outro", "duration_s": 5, "props": { "cta": "Subscribe" } }
  ]
}
```

- **Versioning**: bump `version` on any breaking change; old renders can
  still be rebuilt against their original template row.
- **Scene registry**: each `type` maps to a component/class. New scene
  types are additive.
- **Deterministic timing**: durations are seconds; frames are derived. No
  more "if counter == FRAME_RATE" bugs.

### 7.3 TTS

Replace `gTTS` (obviously robotic; not enterprise-grade) with:
- **Google Cloud TTS Neural2 / Chirp3** — best price/quality on GCP.
- Optionally **ElevenLabs** for premium voices (more expensive; better for
  brand voice).

Wrap behind a `TTSProvider` protocol; template picks voice by name.

### 7.4 Captions

Emit WebVTT captions from the TTS timing marks (Google Cloud TTS returns
them). Upload alongside the mp4; supply to YouTube on publish for
accessibility + SEO.

---

## 8. LLM/extraction deep-dive

### 8.1 Model choice

- **Default: `claude-sonnet-5`** — strong reasoning, structured output,
  cheap enough for this workload.
- **Escalation path**: `claude-opus-5` for high-stakes source material or
  when self-critique flags an unusually high rejection rate.
- **Never**: use a smaller model to "save cost" on the extraction pass —
  question quality is the whole product.

### 8.2 Prompting

- **System prompt** (cached via prompt caching):
  - The task description.
  - The full JSON schema (also enforced via tool use).
  - Difficulty rubric with concrete examples per level.
  - Exam taxonomy the questions can be tagged against (NEET, UPSC, SAT, etc.).
  - "Ground every question in a verbatim source_span" rule (for provenance
    and to reduce hallucination).
- **Tool use** for output — force valid JSON, validate with `pydantic`
  before writing to DB.
- **Two-pass**: extraction pass, then a critic pass that scores each
  question. Below-threshold questions are still stored with
  `status = 'draft'` and `quality_score` low — reviewer decides, not the
  system.

### 8.3 Budget & rate limiting

- Per-source USD cap enforced in the extractor before every call.
- Per-day global cap in Secret Manager, checked before each call.
- Exponential backoff on 429s; circuit breaker per model.

---

## 9. YouTube publishing

### 9.1 Auth

- OAuth 2.0, refresh token in Secret Manager.
- Rotate refresh token on any suspected exposure.
- One OAuth client per environment (dev/stg/prod) mapped to distinct
  YouTube channels.

### 9.2 Quota reality check

YouTube Data API v3 defaults:
- **10,000 units/day per project**.
- **1,600 units per video upload**.
- ⇒ **~6 uploads/day/project** out of the box.

Options:
- Request a quota extension from Google (real form, real review; not
  guaranteed and takes weeks).
- Shard across projects — operationally painful, arguably ToS-adjacent.
- **Design assuming the default cap** and pace uploads accordingly — this
  aligns with the anti-spam story anyway.

### 9.3 Metadata

- Title: templated but human-approved (`title` on `publications`).
- Description: templated with source attribution + timestamps per question.
- Tags: derived from `questions.topics` + `applicable_exams`.
- Thumbnail: auto-generated from render, human can override.
- Visibility: **`private` by default**; reviewer flips to `public`. No
  auto-publish in v1.
- Set `madeForKids = false` unless explicitly targeting that market
  (COPPA implications).

---

## 10. Infrastructure

- **IaC**: Terraform (or Pulumi if you prefer TS). Everything — Cloud Run
  services, Jobs, Pub/Sub topics/subs, Cloud SQL, GCS buckets, IAM,
  secrets — in Terraform. No click-ops in prod.
- **Environments**: `dev`, `staging`, `prod` as separate GCP projects.
- **CI/CD**: Cloud Build (or GitHub Actions with WIF). On merge to `main`:
  build image → push to Artifact Registry → deploy to `dev` → run smoke
  tests → manual promote to `staging`/`prod`.
- **Networking**: private VPC; Cloud SQL only reachable via private IP or
  Auth Proxy; Serverless VPC Connector for Cloud Run.

---

## 11. Observability

- **Structured logs** (JSON) → Cloud Logging; every log line carries
  `trace_id`, `render_id` / `source_id` / `question_set_id` where
  applicable.
- **Distributed tracing** with OpenTelemetry → Cloud Trace. Trace the
  full journey source → extraction → render → publish.
- **Metrics** → Cloud Monitoring. Key SLIs:
  - Extraction success rate.
  - Extraction latency p50/p95.
  - Render success rate.
  - Render duration per minute of video output.
  - Publish success rate.
  - Daily quota consumption (YouTube, Claude API).
- **Alerts**:
  - DLQ non-empty for > 5 min.
  - Render failure rate > 5% over 1h.
  - YouTube quota > 80% consumed.
  - Extraction spend > daily budget.
- **Error tracking**: Sentry or Cloud Error Reporting.

---

## 12. Security

- **Service accounts**: one per service, least-privilege IAM. Renderer
  can `roles/storage.objectAdmin` on the renders prefix only; publisher
  gets `iam.serviceAccountUser` on the YouTube-scoped SA only.
- **Secrets** in Secret Manager (Claude API key, YouTube refresh token,
  DB password). Never in env vars or config files.
- **No secrets in git** — pre-commit hook (`gitleaks`) + CI scan.
- **PII**: none expected; if source content contains PII (rare for public
  articles), do not persist to logs.
- **Content moderation**: run extractor output through a lightweight
  policy check (banned topics list; can layer Claude with a moderation
  system prompt or Perspective API).

---

## 13. Cost model (order-of-magnitude, 100 videos/month)

| Line item                              | Est. monthly cost |
|----------------------------------------|-------------------|
| Cloud Run services (mostly idle)       | $10–30            |
| Cloud Run Jobs (renderer, ~5min × 100) | $10–20            |
| Cloud SQL Postgres (db-g1-small)       | $25–50            |
| GCS (100GB standard + lifecycle)       | $5–10             |
| Pub/Sub                                | <$5               |
| Cloud Logging/Trace/Monitoring         | $5–20             |
| Claude API (~100 sets × ~50k tokens)   | $30–100           |
| Google Cloud TTS                       | $10–30            |
| YouTube API                            | Free (quota-bound)|
| **Total**                              | **~$100–300/mo**  |

Rendering GPU is **not** required at this scale. If you push to thousands
of videos/mo, move renderer to Cloud Batch on GPU-backed VMs and expect
this line item to dominate.

---

## 14. Pitfalls & mitigations

1. **YouTube spam/auto-gen policy** — the biggest business risk.
   *Mitigation*: mandatory human review, differentiated production values
   (this is why Remotion matters), spaced uploads, real channel
   branding/community, don't upload the same template output shape 100×
   in a row. Assume 2–5% termination risk regardless; keep prod GCS
   renders so a channel switch is a config change, not a re-render.
2. **YouTube quota (1600 units/upload)** — see §9.2. Don't design a
   fire-hose; design a drip.
3. **LLM hallucination** — questions grounded in `source_span`;
   two-pass critique; human review before public upload.
4. **Copyright of source articles** — questions are transformative but
   avoid verbatim article text; retain source attribution in video
   description; **maintain a domain allow-list** (bias to public-domain
   or clearly-permissive sources initially).
5. **Cloud Run cold starts on extractor/renderer** — extractor can
   tolerate; renderer is a Job so this doesn't apply.
6. **60-min HTTP timeout on Cloud Run services** — Jobs for anything
   long-running; never render inside a service.
7. **Pub/Sub retry storms** — every handler idempotent; DLQ configured;
   push subscription concurrency bounded.
8. **Cloud SQL always-on cost** — the one non-serverless line item; live
   with it or accept the operational cost of Cloud SQL Studio/Alloy for
   scale-to-zero.
9. **Non-deterministic renders** — pin the renderer container by digest
   (not tag); pin fonts and ffmpeg version; record everything in
   `manifest.json`.
10. **Voice quality with `gTTS`** — retire it. Users can tell.
11. **Prompt injection via source content** — a scraped article could
    include "ignore previous instructions" text; treat all source content
    as data, not instructions, and structure the prompt so the model
    knows the source block is untrusted.
12. **Silent renderer failures** — every render writes a `manifest.json`
    and structured logs; a failed render leaves the row in `failed`
    status with `error` populated; never silent success on partial
    output.

---

## 15. Phased rollout

### Phase A — Foundation (2–3 weeks)
- Terraform for the GCP project, GCS buckets, Cloud SQL, Pub/Sub topics.
- API skeleton + Postgres schema + Alembic migrations.
- CI/CD pipeline; dev environment stood up.
- **No LLM, no renderer yet** — end-state: you can `POST /sources` and
  see a row in the DB.

### Phase B — Extraction path (2 weeks)
- Source ingestor with the `TextAdapter` and `ArticleUrlAdapter`.
- Extractor worker with Claude Sonnet 5 + structured output + critique.
- Reviewer UI (minimal: list, approve, reject, edit).
- **End-state**: paste a URL, get reviewable questions in the UI.

### Phase C — Rendering path (3–4 weeks)
- Pick renderer tech (Remotion vs MoviePy) and prototype one template.
- Cloud Run Job for the renderer.
- Render orchestrator + `render.requested` → Job execution.
- **End-state**: click "Render" on an approved question set, get an mp4
  in GCS 5 minutes later.

### Phase D — Publishing (1–2 weeks)
- Publisher service with OAuth flow, quota accounting, idempotency.
- **End-state**: click "Publish" and the video goes live on YouTube
  (as `private` at first; flip to `public` from the UI).

### Phase E — Automation & scale (ongoing)
- RSS/website adapters.
- Scheduled ingestion.
- Additional templates.
- Additional platforms (Shorts, Reels).
- Multi-language.

---

## 16. Open questions (need decisions before Phase A)

1. **Renderer tech**: Remotion or MoviePy? (Recommend Remotion.)
2. **Reviewer UI framework**: Next.js or a lighter admin (e.g. Retool)?
3. **TTS provider**: Google Cloud TTS or ElevenLabs (or both, template-selectable)?
4. **Language**: Python for all services, or TS for the renderer + Python for the rest?
5. **Initial source allow-list**: which domains are in scope for MVP?
6. **Channel strategy**: one YouTube channel per topic vertical, or one
   channel with playlists? (Affects quota planning and brand risk.)
7. **Human reviewer SLA**: how fast must review happen before renders
   go stale? Drives whether we notify Slack, page, etc.
8. **Data retention**: how long do we keep failed renders, rejected
   questions, source snapshots? Drives GCS lifecycle and Postgres
   partitioning.

---

## 17. What this design deliberately doesn't do

- **No custom LLM training** — off-the-shelf Claude Sonnet 5 is enough;
  fine-tuning is a v3 concern once you have a rejection-reason corpus
  from the reviewer feedback loop.
- **No real-time collaboration** in the reviewer UI — single-editor
  optimistic locking is fine at this scale.
- **No multi-tenant isolation** — single-org DB; add row-level security
  and per-tenant GCS prefixes only when you have a second customer.
- **No self-hosted anything** — this is Cloud Run + managed services on
  purpose; the moment you have a Kubernetes cluster, you have an ops
  team.

---

## 18. Future: multi-modal delivery (test env, flashcards, more)

The v2 architecture deliberately treats **extraction as the moat** and
**delivery formats as pluggable consumers** of the shared
`question_sets` / `questions` tables. The video renderer is the first
consumer; several others are natural extensions:

```
source → extraction → questions in DB ─┬─► video renderer      (v2, planned)
                                        ├─► test runner         (this section)
                                        ├─► flashcard generator (later)
                                        └─► podcast / audio     (later)
```

### 18.1 Motivating scenario

A student covers a topic, uploads the PDF / notes / article to TesVi,
and gets an **interactive test session in the browser** — same
extraction pipeline, different terminal delivery format. No video, no
YouTube, no reviewer approval needed for their own private use.

Longer-term this could be the *primary* B2C product, with video as a
marketing/acquisition surface — but that's a business decision, not an
architectural one. The design supports either framing.

### 18.2 What v2 already gets right for this

- Extraction is delivery-mode-agnostic (see rule in §3).
- `sources.owner_id` + `sources.visibility` (added in §4.1) support
  user-scoped ingestion from day one.
- `question_sets` splits `extraction_status` (pipeline state) from
  `publish_status` (public-delivery gate, §4.2). Private/self-consumption
  only needs the former.
- Source adapters are polymorphic; adding a `PdfAdapter` /
  `UserUploadAdapter` is a new class, not a pipeline change.

### 18.3 What's genuinely new when we build it

**New services / infra**:
- **`test-runner`** — Cloud Run service; stateful per active session
  (Memorystore/Redis for hot state, Postgres for durable records).
  Handles: start attempt, deliver next question, record answer, compute
  score, resume mid-session.
- **External auth** — Firebase Auth or Identity Platform (Google sign-in
  at minimum). v2's IAP-only model assumes internal users; students are
  external.
- **Web frontend** — Next.js app, separate from the reviewer UI.
- **`PdfAdapter`** in source-ingestor — one new class; PDF text
  extraction via `pypdfium2` or Google Document AI for scanned PDFs.

**New tables**:

```sql
-- 18.a Users
create table users (
  id           uuid primary key default gen_random_uuid(),
  email        text not null unique,
  display_name text,
  auth_provider text not null,        -- 'google','password',...
  external_uid  text not null,        -- provider's user id
  plan          text not null default 'free'
                    check (plan in ('free','pro','edu')),
  created_at   timestamptz not null default now(),
  metadata     jsonb not null default '{}'::jsonb,
  unique (auth_provider, external_uid)
);

-- 18.b Test templates: quiz-taking config (analog of video_templates)
create table test_templates (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  version       int not null,
  spec          jsonb not null,   -- time_limit_s, shuffle, hints, negative_marks, review_mode
  created_at    timestamptz not null default now(),
  unique (name, version)
);

-- 18.c Attempts: one per user × question_set × start
create table test_attempts (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references users(id),
  question_set_id  uuid not null references question_sets(id),
  test_template_id uuid not null references test_templates(id),
  status           text not null default 'in_progress'
                       check (status in ('in_progress','submitted','abandoned','expired')),
  started_at       timestamptz not null default now(),
  submitted_at     timestamptz,
  time_limit_s     int,
  score            numeric(6,2),
  max_score        numeric(6,2),
  metadata         jsonb not null default '{}'::jsonb
);
create index on test_attempts (user_id, started_at desc);

-- 18.d Per-question answers within an attempt
create table attempt_answers (
  id                 uuid primary key default gen_random_uuid(),
  attempt_id         uuid not null references test_attempts(id) on delete cascade,
  question_id        uuid not null references questions(id),
  selected_options   text[] not null default '{}',
  is_correct         boolean,
  time_spent_ms      int,
  answered_at        timestamptz not null default now(),
  unique (attempt_id, question_id)
);
```

### 18.4 Policy differences from the video product

- **No reviewer approval required** for owner-self-consumption. Enforced
  at the API: the test-runner accepts any `question_set` where
  `owner_id = current_user_id AND extraction_status = 'extracted'`,
  regardless of `publish_status`.
- **Per-user extraction budgets** — the current per-source/per-day caps
  aren't enough once students self-serve; add per-user daily/monthly
  token caps stored on the `users` row (or a `user_usage` table). Free
  tier could hallucinate a $500 bill in an afternoon otherwise.
- **YouTube-specific risks don't apply** — this surface is much lower
  policy risk than mass-upload video.
- **PII posture changes** — users have accounts, so this becomes a
  real product that needs a privacy policy, GDPR/DPDP handling, data
  export/delete flows. None of that is in scope for v2.

### 18.5 What NOT to build into v2 for this

Resist the temptation to pre-build test-env plumbing during Phase A–D:

- Don't add `users` / attempts tables until you actually build the
  test-runner. Empty tables rot.
- Don't add Firebase Auth until then; IAP is fine for the internal v2.
- Don't split the API into "internal" and "public" versions yet — do
  that when the second consumer exists.

The **only** things we do now to keep the door open are the schema
adjustments already folded into §4 (`owner_id`, `visibility`, split
`publish_status` from `extraction_status`) and the delivery-agnostic
rule on the extractor (§3.3). Everything else is deferred until we
commit to building it.
