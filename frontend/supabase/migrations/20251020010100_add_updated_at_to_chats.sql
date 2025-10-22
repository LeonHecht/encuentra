-- Add updated_at and keep it fresh

alter table public.chats
  add column if not exists updated_at timestamptz not null default now();

create or replace function public.set_chat_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end; $$ language plpgsql;

drop trigger if exists t_chats_updated_at on public.chats;
create trigger t_chats_updated_at
before update on public.chats
for each row execute function public.set_chat_updated_at();

-- Optional: bump chat recency when a new message is added
create or replace function public.bump_chat_updated_at()
returns trigger as $$
begin
  update public.chats set updated_at = now() where id = new.chat_id;
  return new;
end; $$ language plpgsql;

drop trigger if exists t_messages_bump_chat_updated_at on public.chat_messages;
create trigger t_messages_bump_chat_updated_at
after insert on public.chat_messages
for each row execute function public.bump_chat_updated_at();

-- Optional index for fast "recent chats" queries
create index if not exists idx_chats_updated_at on public.chats (updated_at desc);