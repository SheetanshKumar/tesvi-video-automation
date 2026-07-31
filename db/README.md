# Database

The v2 system of record is Postgres (Cloud SQL in prod, local Docker in dev).
See [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) §4 for the data model
rationale and §18 for the deferred multi-tenancy pieces (users table,
attempts).

## Migrations

Managed with [`golang-migrate`](https://github.com/golang-migrate/migrate).
Files in `migrations/` follow the convention:

```
NNNN_short_description.up.sql
NNNN_short_description.down.sql
```

Rules:

- **Sequential numbering** (`0001`, `0002`, ...).
- **One logical change per migration** — one table, or one focused schema
  change. Keeps PR review scoped.
- **Reversible** — every `up.sql` has a matching `down.sql`. A migration
  without a working rollback is a footgun in production.
- **Never edit an applied migration** in-place; create a new one.

## Current schema

| # | Migration               | Adds                                        |
|---|-------------------------|---------------------------------------------|
| 1 | `extensions`            | `pgcrypto` (for `gen_random_uuid()`)        |
| 2 | `sources`               | Raw ingested content, per-owner dedup       |
| 3 | `question_sets`         | Batches of MCQs; two-axis status            |
| 4 | `questions`             | Individual MCQs with metadata               |
| 5 | `video_templates`       | Versioned template specs                    |
| 6 | `renders`               | Render attempts, keyed by input fingerprint |
| 7 | `publications`          | Platform uploads (YouTube, etc.)            |
| 8 | `idempotency_keys`      | Short-lived dedup for external actions      |
| 9 | `audit_events`          | Append-only action log                      |

## Local development

Install `migrate`:

```bash
brew install golang-migrate
```

Start local Postgres:

```bash
make db-up
```

Run all migrations:

```bash
make migrate-up
```

Roll back one step:

```bash
make migrate-down
```

Create a new migration pair:

```bash
make migrate-create name=add_users_table
```

## Connection string

Default local connection (see [`.env.example`](../.env.example)):

```
postgres://tesvi:tesvi@localhost:5432/tesvi?sslmode=disable
```

## Seeds

`seeds/` is reserved for reference data (e.g. a starter set of
`video_templates`) once the renderer exists. Empty for now.
