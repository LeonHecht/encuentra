-- Ensure gen_random_uuid() is available
create extension if not exists "pgcrypto";

-- Create spaces table
create table if not exists public.spaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_id uuid not null references auth.users(id) on delete cascade,
  org_id uuid references public.orgs(id),
  is_public boolean default false,
  storage_bucket text default 'user-uploads',
  storage_path text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists spaces_owner_id_created_at_idx on public.spaces (owner_id, created_at desc);
create index if not exists spaces_org_id_idx on public.spaces (org_id) where org_id is not null;

-- Enable RLS
alter table public.spaces enable row level security;

-- Recreate policies (drop if they already exist)
drop policy if exists "users can view their own spaces" on public.spaces;
drop policy if exists "users can create their own spaces" on public.spaces;
drop policy if exists "users can update their own spaces" on public.spaces;
drop policy if exists "users can delete their own spaces" on public.spaces;

-- Minimal policies (no org membership yet)
create policy "users can view their own spaces"
on public.spaces
for select
using (
  owner_id = auth.uid()
  or is_public = true
);

create policy "users can create their own spaces"
on public.spaces
for insert
with check (owner_id = auth.uid());

create policy "users can update their own spaces"
on public.spaces
for update
using (owner_id = auth.uid())
with check (owner_id = auth.uid());

create policy "users can delete their own spaces"
on public.spaces
for delete
using (owner_id = auth.uid());