-- Add per-chat agent state to persist agentic reasoning context
alter table public.chats
  add column if not exists agent_state jsonb;