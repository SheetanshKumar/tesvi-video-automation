-- Questions: individual MCQs within a question set.
-- See docs/ARCHITECTURE.md §4.3.
create table questions (
    id                     uuid primary key default gen_random_uuid(),
    question_set_id        uuid not null references question_sets(id) on delete cascade,
    ordinal                int not null,
    question_text          text not null,
    -- options: {"A": "..", "B": "..", ...}
    options                jsonb not null,
    -- correct_options: array of option keys, e.g. ['A'] or ['A','C'] when multi_correct.
    correct_options        text[] not null,
    multi_correct          boolean not null default false,
    explanation            text,
    difficulty             text not null
                                check (difficulty in ('easy','medium','hard','expert')),
    topics                 text[] not null default '{}',
    applicable_exams       text[] not null default '{}',
    bloom_level            text
                                check (bloom_level in
                                       ('remember','understand','apply','analyze','evaluate','create')),
    estimated_time_seconds int not null default 30,
    -- source_span: verbatim snippet the question is grounded in (provenance).
    source_span            text,
    -- quality_score: 0.00-1.00 from LLM self-critique or reviewer.
    quality_score          numeric(3,2)
                                check (quality_score is null
                                       or (quality_score >= 0 and quality_score <= 1)),
    status                 text not null default 'draft'
                                check (status in ('draft','approved','rejected')),
    rejection_reason       text,
    created_at             timestamptz not null default now(),
    metadata               jsonb not null default '{}'::jsonb,
    unique (question_set_id, ordinal)
);

create index questions_topics_idx on questions using gin (topics);
create index questions_exams_idx on questions using gin (applicable_exams);
create index questions_difficulty_idx on questions (difficulty);
create index questions_status_idx on questions (status);
