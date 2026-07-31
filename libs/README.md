# Shared libraries

Per-language shared code lives here. Kept intentionally thin — prefer
duplicating simple utilities across services over premature abstraction.
A library only earns its place here once at least two services need it.

```
libs/
├── go/         # Go modules importable by Go services
├── python/     # Python packages importable by Python services
└── ts/         # TypeScript packages importable by TS services
```

Likely first residents (do not create speculatively):

- `libs/go/tesvi-db` — shared `pgx` pool wiring + migration helpers.
- `libs/go/tesvi-pubsub` — thin wrapper over the GCP Pub/Sub client with
  the standard structured-log + idempotency-key pattern.
- `libs/go/tesvi-obs` — logging, tracing, and metrics init boilerplate.
- `libs/python/tesvi-obs` — same for Python services.
- `libs/ts/tesvi-schema` — shared TypeScript types generated from the
  Postgres schema, consumed by `renderer` and `reviewer-ui`.

Nothing is scaffolded yet — this PR only defines the layout.
