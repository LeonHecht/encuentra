create table if not exists public.chat_message_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  chat_id uuid not null references public.chats(id) on delete cascade,
  assistant_message_id uuid not null references public.chat_messages(id) on delete cascade,
  space text,
  previous_user_message text,
  previous_messages jsonb not null default '[]'::jsonb,
  assistant_response text not null,
  citations jsonb not null default '[]'::jsonb,
  feedback text not null check (feedback in ('positive', 'negative')),
  feedback_text text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, assistant_message_id)
);

create index if not exists chat_message_feedback_user_created_idx
on public.chat_message_feedback (user_id, created_at desc);

create index if not exists chat_message_feedback_chat_idx
on public.chat_message_feedback (chat_id, created_at desc);

create index if not exists chat_message_feedback_label_idx
on public.chat_message_feedback (feedback);

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end; $$ language plpgsql;

drop trigger if exists t_chat_message_feedback_updated_at on public.chat_message_feedback;
create trigger t_chat_message_feedback_updated_at
before update on public.chat_message_feedback
for each row execute function public.set_updated_at();

alter table public.chat_message_feedback enable row level security;

create policy "users can insert their own chat feedback"
on public.chat_message_feedback
for insert
with check (
  user_id = auth.uid()
  and exists (
    select 1 from public.chats c
    where c.id = chat_id and c.user_id = auth.uid()
  )
  and exists (
    select 1 from public.chat_messages m
    where m.id = assistant_message_id
      and m.chat_id = chat_id
      and m.role = 'assistant'
  )
);

create policy "users can view their own chat feedback"
on public.chat_message_feedback
for select
using (user_id = auth.uid());

create policy "users can update their own chat feedback"
on public.chat_message_feedback
for update
using (user_id = auth.uid())
with check (
  user_id = auth.uid()
  and exists (
    select 1 from public.chats c
    where c.id = chat_id and c.user_id = auth.uid()
  )
  and exists (
    select 1 from public.chat_messages m
    where m.id = assistant_message_id
      and m.chat_id = chat_id
      and m.role = 'assistant'
  )
);
