# Services

Each service is independently deployable to Cloud Run (Services or Jobs).
See [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) §3 for
responsibilities and boundaries.

## Language policy

Polyglot on purpose — each service is a self-contained container, so
language boundaries never bleed across services.

| Service               | Language   | Runtime           | Rationale                                      |
|-----------------------|------------|-------------------|------------------------------------------------|
| `api`                 | Go         | Cloud Run Service | HTTP + DB + Pub/Sub; cheap cold starts         |
| `source-ingestor`     | Go         | Cloud Run Service | Fetch/parse; small footprint                   |
| `extractor`           | Python     | Cloud Run Service | Anthropic SDK, tokenization, chunking          |
| `render-orchestrator` | Go         | Cloud Run Service | Thin control-plane                             |
| `renderer`            | TypeScript | Cloud Run Job     | Remotion (React-based programmatic video)      |
| `publisher`           | Go         | Cloud Run Service | HTTP + YouTube Data API + Pub/Sub              |
| `reviewer-ui`         | TypeScript | Cloud Run Service | Next.js frontend behind IAP                    |

**Why Go for the HTTP/orchestration layer**: Cloud Run cold starts of
~500ms (vs Python's 2–5s), tiny images (10–30 MB vs 200–500 MB),
type-safe DB access via `sqlc` + `pgx`, and cheaper per-request memory.
The one place it's weaker is the LLM ecosystem — hence Python for the
extractor specifically.

## Standard layout (per service, once scaffolded)

Go services:

```
services/<name>/
├── cmd/<name>/main.go        # entrypoint
├── internal/                  # non-exported implementation
│   ├── handler/               # HTTP / Pub/Sub handlers
│   ├── store/                 # DB access (sqlc-generated)
│   └── config/                # env loading
├── sql/queries/               # sqlc input queries
├── Dockerfile
├── go.mod
├── sqlc.yaml
└── README.md
```

Python services:

```
services/<name>/
├── src/<name>/                # package
├── tests/
├── Dockerfile
├── pyproject.toml
└── README.md
```

TypeScript services:

```
services/<name>/
├── src/
├── tests/
├── Dockerfile
├── package.json
├── tsconfig.json
└── README.md
```

## Status

All seven services have runnable skeletons: each builds/typechecks and
exposes `/healthz` (except `renderer`, which is a Cloud Run Job invoked
via `RENDER_ID` env var, not HTTP). None contain real business logic
yet — that lands per-phase per
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) §15.

Sanity commands from repo root:

```bash
make go-build       # builds api / source-ingestor / render-orchestrator / publisher
make ts-typecheck   # typechecks renderer + reviewer-ui (needs `make ts-install` first)
make py-install     # installs extractor into current Python env
make py-test        # runs extractor smoke tests
```
