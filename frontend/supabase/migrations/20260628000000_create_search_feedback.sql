create table if not exists public.search_query_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  query_text text not null,
  space text not null,
  top_k int,
  year_filter int,
  result_count int not null default 0,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists search_query_logs_user_created_idx
on public.search_query_logs (user_id, created_at desc);

create index if not exists search_query_logs_query_idx
on public.search_query_logs (query_text, space);

alter table public.search_query_logs enable row level security;

create policy "users can insert their own search query logs"
on public.search_query_logs
for insert
with check (user_id = auth.uid());

create policy "users can view their own search query logs"
on public.search_query_logs
for select
using (user_id = auth.uid());

create table if not exists public.search_result_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  query_log_id uuid references public.search_query_logs(id) on delete set null,
  query_text text not null,
  space text not null,
  top_k int,
  year_filter int,
  doc_id text not null,
  rank int not null,
  score double precision,
  title text,
  snippet text,
  feedback text not null check (feedback in ('positive', 'negative')),
  reason text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, query_text, space, doc_id)
);

create index if not exists search_result_feedback_user_created_idx
on public.search_result_feedback (user_id, created_at desc);

create index if not exists search_result_feedback_query_idx
on public.search_result_feedback (query_text, space);

create index if not exists search_result_feedback_doc_idx
on public.search_result_feedback (space, doc_id);

create index if not exists search_result_feedback_label_idx
on public.search_result_feedback (feedback);

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end; $$ language plpgsql;

drop trigger if exists t_search_result_feedback_updated_at on public.search_result_feedback;
create trigger t_search_result_feedback_updated_at
before update on public.search_result_feedback
for each row execute function public.set_updated_at();

alter table public.search_result_feedback enable row level security;

create policy "users can insert their own search feedback"
on public.search_result_feedback
for insert
with check (
  user_id = auth.uid()
  and (
    query_log_id is null
    or exists (
      select 1 from public.search_query_logs q
      where q.id = query_log_id and q.user_id = auth.uid()
    )
  )
);

create policy "users can view their own search feedback"
on public.search_result_feedback
for select
using (user_id = auth.uid());

create policy "users can update their own search feedback"
on public.search_result_feedback
for update
using (user_id = auth.uid())
with check (
  user_id = auth.uid()
  and (
    query_log_id is null
    or exists (
      select 1 from public.search_query_logs q
      where q.id = query_log_id and q.user_id = auth.uid()
    )
  )
);
