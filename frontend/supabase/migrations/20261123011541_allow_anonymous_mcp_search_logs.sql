alter table public.search_query_logs
  alter column user_id drop not null,
  add constraint search_query_logs_anonymous_mcp_source
  check (user_id is not null or (metadata ->> 'source') is not distinct from 'mcp');
