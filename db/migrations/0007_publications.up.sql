-- Publications: uploads of rendered videos to external platforms.
-- See docs/ARCHITECTURE.md §4.6.
create table publications (
    id           uuid primary key default gen_random_uuid(),
    render_id    uuid not null references renders(id),
    platform     text not null
                        check (platform in ('youtube','instagram_reels','tiktok','shorts')),
    external_id  text,
    external_url text,
    title        text not null,
    description  text,
    tags         text[],
    visibility   text not null default 'private'
                        check (visibility in ('public','unlisted','private')),
    status       text not null default 'pending'
                        check (status in ('pending','uploading','uploaded','failed','removed')),
    uploaded_at  timestamptz,
    error        text,
    metadata     jsonb not null default '{}'::jsonb
);

-- At most one active (uploading or uploaded) publication per (render, platform).
-- Failed / removed publications are allowed to coexist so we retain history.
create unique index publications_active_uniq
    on publications (render_id, platform)
    where status in ('uploading','uploaded');
