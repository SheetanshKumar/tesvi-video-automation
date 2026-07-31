-- Audit events: append-only log of state transitions and human/system actions.
-- See docs/ARCHITECTURE.md §4.8.
create table audit_events (
    id        bigserial primary key,
    actor     text not null,        -- 'system:extractor', 'user:someone@example.com'
    action    text not null,        -- 'questions.approved', 'render.started', ...
    entity    text not null,        -- 'question_set', 'render', 'publication'
    entity_id uuid not null,
    payload   jsonb not null default '{}'::jsonb,
    at        timestamptz not null default now()
);

create index audit_events_entity_idx on audit_events (entity, entity_id, at desc);
create index audit_events_at_idx on audit_events (at desc);
