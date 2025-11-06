-- Ensure updated_at exists and stays fresh on updates for key tables

-- 1) Generic trigger function to set NEW.updated_at = now()
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end; $$ language plpgsql;

-- 2) user_profiles: ensure column and trigger
alter table if exists public.user_profiles
  add column if not exists updated_at timestamptz not null default now();

drop trigger if exists t_user_profiles_updated_at on public.user_profiles;
create trigger t_user_profiles_updated_at
before update on public.user_profiles
for each row execute function public.set_updated_at();

-- 3) spaces: ensure column and trigger
alter table if exists public.spaces
  add column if not exists updated_at timestamptz not null default now();

drop trigger if exists t_spaces_updated_at on public.spaces;
create trigger t_spaces_updated_at
before update on public.spaces
for each row execute function public.set_updated_at();

-- 4) user_settings: ensure column and trigger
alter table if exists public.user_settings
  add column if not exists updated_at timestamptz not null default now();

drop trigger if exists t_user_settings_updated_at on public.user_settings;
create trigger t_user_settings_updated_at
before update on public.user_settings
for each row execute function public.set_updated_at();
