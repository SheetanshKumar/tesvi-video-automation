-- Sources: raw inputs (text, article URLs, RSS items, websites, PDFs, user uploads).
-- See docs/ARCHITECTURE.md §4.1.
create table sources (
    id                  uuid primary key default gen_random_uuid(),
    type                text not null
                            check (type in ('text','article_url','rss_item','website','pdf','user_upload')),
    uri                 text,
    raw_content_gcs_uri text not null,
    content_hash        text not null,
    title               text,
    author              text,
    published_at        timestamptz,
    ingested_at         timestamptz not null default now(),
    ingest_status       text not null default 'pending'
                            check (ingest_status in ('pending','fetched','failed','skipped')),
    ingest_error        text,
    -- owner_id is NOT yet FK'd to users(id): the users table is deferred until
    -- we build the test-env product (see docs/ARCHITECTURE.md §18). Add the FK
    -- constraint in that migration.
    owner_id            uuid,
    visibility          text not null default 'private'
                            check (visibility in ('private','org','public')),
    metadata            jsonb not null default '{}'::jsonb
);

create index sources_type_ingested_at_idx on sources (type, ingested_at desc);
create index sources_owner_id_idx on sources (owner_id) where owner_id is not null;

-- Dedup semantics differ by ownership:
--   * User-owned sources: unique per (owner, content_hash) — two users can
--     each upload the same PDF and keep independent rows.
--   * System-owned sources (owner_id IS NULL): globally unique on content_hash.
-- A plain `unique (owner_id, content_hash)` would fail to enforce the second
-- rule because Postgres treats NULLs as distinct in unique constraints.
create unique index sources_owner_content_hash_uniq
    on sources (owner_id, content_hash) where owner_id is not null;
create unique index sources_system_content_hash_uniq
    on sources (content_hash) where owner_id is null;
