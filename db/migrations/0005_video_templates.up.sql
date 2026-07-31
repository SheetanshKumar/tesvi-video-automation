-- Video templates: versioned JSON specs describing scenes, transitions,
-- and animation intent. Interpreted by the renderer at runtime — never
-- hardcoded in service code. See docs/ARCHITECTURE.md §7.2.
create table video_templates (
    id         uuid primary key default gen_random_uuid(),
    name       text not null,
    version    int not null check (version > 0),
    spec       jsonb not null,
    created_at timestamptz not null default now(),
    created_by text,
    unique (name, version)
);
