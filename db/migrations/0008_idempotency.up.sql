-- Idempotency keys for external side-effectful actions (YouTube uploads,
-- render enqueues). See docs/ARCHITECTURE.md §4.7.
--
-- Rows are short-lived: a scheduled cleanup should DELETE where expires_at < now().
create table idempotency_keys (
    key        text primary key,
    scope      text not null,       -- e.g. 'youtube_upload', 'render_request'
    entity_id  uuid not null,
    created_at timestamptz not null default now(),
    expires_at timestamptz not null
);

create index idempotency_keys_expires_at_idx on idempotency_keys (expires_at);
