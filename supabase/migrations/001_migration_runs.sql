-- Stores contract metadata only. Never send raw SOAP payloads or credentials here.
create table if not exists public.migration_runs (
    id bigint generated always as identity primary key,
    source_id text not null,
    analysis jsonb not null,
    created_at timestamptz not null default now()
);

alter table public.migration_runs enable row level security;

-- No public policies: the backend service role is the only writer.
grant usage on schema public to service_role;
grant insert on table public.migration_runs to service_role;
grant usage, select on sequence public.migration_runs_id_seq to service_role;
