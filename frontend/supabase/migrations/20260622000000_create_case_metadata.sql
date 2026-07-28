create table if not exists public.case_metadata (
  space text not null,
  doc_id text not null,
  status text not null default 'pending' check (status in ('pending', 'ready', 'failed')),
  source_hash text,
  model text,
  metadata jsonb,
  error text,
  attempt_count int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (space, doc_id)
);

create index if not exists case_metadata_status_updated_idx
on public.case_metadata (status, updated_at desc);

alter table public.case_metadata enable row level security;
