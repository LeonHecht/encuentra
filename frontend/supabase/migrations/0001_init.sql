-- Users (your app profile; identity lives in auth.users)
create table public.user_profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  avatar_url text,
  country text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Organizations (optional now, future-proofing)
create table public.orgs (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now()
);

create table public.members (
  user_id uuid not null references auth.users(id) on delete cascade,
  org_id uuid not null references public.orgs(id) on delete cascade,
  role text not null check (role in ('owner','admin','member')),
  created_at timestamptz not null default now(),
  primary key (user_id, org_id)
);

-- Spaces (for document organization)
create table public.spaces (
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

create index on public.spaces (owner_id, created_at desc);
create index on public.spaces (org_id) where org_id is not null;

-- Files (track uploaded documents)
create table public.files (
  id uuid primary key default gen_random_uuid(),
  space_id uuid not null references public.spaces(id) on delete cascade,
  filename text not null,
  storage_path text not null,
  file_size bigint,
  mime_type text,
  uploaded_by uuid not null references auth.users(id),
  indexed boolean default false,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index on public.files (space_id, created_at desc);
create index on public.files (uploaded_by, created_at desc);

-- Chats & messages
create table public.chats (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  org_id uuid references public.orgs(id),
  title text,
  created_at timestamptz not null default now()
);

create index on public.chats (user_id, created_at desc);

create table public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  chat_id uuid not null references public.chats(id) on delete cascade,
  role text not null check (role in ('user','assistant','system')),
  content text not null,
  meta jsonb, -- tokens, model, latency, etc.
  created_at timestamptz not null default now()
);

create index on public.chat_messages (chat_id, created_at);

-- Settings (keep it flexible with JSONB)
create table public.user_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  prefs jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

-- Payments (placeholder; wire to Stripe later)
create table public.payment_accounts (
  user_id uuid primary key references auth.users(id) on delete cascade,
  provider text not null default 'stripe',
  provider_customer_id text,
  subscription_tier text default 'free',
  valid_until timestamptz
);


alter table public.user_profiles enable row level security;
alter table public.spaces enable row level security;
alter table public.files enable row level security;
alter table public.chats enable row level security;
alter table public.chat_messages enable row level security;
alter table public.user_settings enable row level security;
alter table public.payment_accounts enable row level security;

-- Helpers:
-- auth.uid() is the UUID from the Supabase-authenticated JWT.

create policy "users can read/write their profile"
on public.user_profiles
for all
using (id = auth.uid())
with check (id = auth.uid());

-- Spaces policies
create policy "users can view their own spaces"
on public.spaces
for select using (
  owner_id = auth.uid() 
  or is_public = true
  or exists (
    select 1 from public.members m 
    where m.user_id = auth.uid() and m.org_id = spaces.org_id
  )
);

create policy "users can create their own spaces"
on public.spaces
for insert with check (owner_id = auth.uid());

create policy "users can update their own spaces"
on public.spaces
for update using (owner_id = auth.uid())
with check (owner_id = auth.uid());

create policy "users can delete their own spaces"
on public.spaces
for delete using (owner_id = auth.uid());

-- Files policies
create policy "users can view files in accessible spaces"
on public.files
for select using (
  exists (
    select 1 from public.spaces s 
    where s.id = files.space_id 
    and (
      s.owner_id = auth.uid() 
      or s.is_public = true
      or exists (
        select 1 from public.members m 
        where m.user_id = auth.uid() and m.org_id = s.org_id
      )
    )
  )
);

create policy "users can upload files to accessible spaces"
on public.files
for insert with check (
  exists (
    select 1 from public.spaces s 
    where s.id = files.space_id 
    and (
      s.owner_id = auth.uid()
      or exists (
        select 1 from public.members m 
        where m.user_id = auth.uid() and m.org_id = s.org_id
      )
    )
  )
);

create policy "users can delete files they uploaded"
on public.files
for delete using (uploaded_by = auth.uid());

create policy "users manage their own chats"
on public.chats
for all
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "messages visible via parent chat"
on public.chat_messages
for select using (
  exists (select 1 from public.chats c where c.id = chat_id and c.user_id = auth.uid())
);
create policy "insert messages if own chat"
on public.chat_messages
for insert with check (
  exists (select 1 from public.chats c where c.id = chat_id and c.user_id = auth.uid())
);

create policy "users manage their settings"
on public.user_settings
for all
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "users view their payment account"
on public.payment_accounts
for select using (user_id = auth.uid());
