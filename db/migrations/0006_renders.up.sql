-- Renders: one row per actual (attempted or completed) video render.
-- See docs/ARCHITECTURE.md §4.5.
create table renders (
    id                uuid primary key default gen_random_uuid(),
    question_set_id   uuid not null references question_sets(id),
    template_id       uuid not null references video_templates(id),
    status            text not null default 'queued'
                            check (status in
                                   ('queued','rendering','succeeded','failed','cancelled')),
    requested_at      timestamptz not null default now(),
    started_at        timestamptz,
    completed_at      timestamptz,
    video_gcs_uri     text,
    thumbnail_gcs_uri text,
    captions_gcs_uri  text,
    duration_seconds  numeric(8,2),
    resolution        text,
    frame_rate        numeric(4,1),
    cost_usd          numeric(10,4),
    error             text,
    -- render_job_name: Cloud Run Job execution id, for cross-linking to
    -- job logs and cancellation.
    render_job_name   text,
    -- input_fingerprint: sha256(questions_snapshot + template_spec + voice + ...).
    -- Renders with the same fingerprint are deduped — same inputs never
    -- render twice for the same (question_set, template) pair.
    input_fingerprint text not null,
    metadata          jsonb not null default '{}'::jsonb,
    unique (question_set_id, template_id, input_fingerprint)
);

create index renders_status_requested_at_idx on renders (status, requested_at);
