-- Question sets: a batch of MCQs generated from one source.
-- See docs/ARCHITECTURE.md §4.2.
--
-- Two independent status axes:
--   extraction_status — pipeline state (did the LLM run successfully?)
--   publish_status    — public-delivery gate (has a human approved?)
--
-- Owner-private surfaces (test-env, personal review) may consume 'extracted'
-- sets without requiring publish_status='approved'. See §18.
create table question_sets (
    id                  uuid primary key default gen_random_uuid(),
    source_id           uuid references sources(id) on delete set null,
    -- owner_id: no FK yet, see 0002_sources.up.sql for rationale.
    owner_id            uuid,
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
    extraction_model    text,
    extraction_cost_usd numeric(10,4),
    reviewed_by         text,
    reviewed_at         timestamptz,
    created_at          timestamptz not null default now(),
    metadata            jsonb not null default '{}'::jsonb
);

create index question_sets_extraction_status_idx on question_sets (extraction_status);
create index question_sets_publish_status_idx on question_sets (publish_status);
create index question_sets_topic_idx on question_sets (topic);
create index question_sets_owner_id_idx on question_sets (owner_id) where owner_id is not null;
