-- Create a trigger to automatically create user_profiles entry when a new user signs up

-- Function to create user profile automatically
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_display_name text;
begin
  -- Build display name from various metadata sources with fallbacks
  v_display_name := coalesce(
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'name',
    new.raw_user_meta_data->>'display_name',
    new.raw_user_meta_data->>'preferred_username',
    new.email,
    'User ' || left(new.id::text, 8)
  );

  -- Create user profile (idempotent with ON CONFLICT)
  insert into public.user_profiles (id, display_name, created_at, updated_at)
  values (new.id, v_display_name, now(), now())
  on conflict (id) do nothing;

  -- Create default "personal" space once per user (prevent duplicates)
  insert into public.spaces (name, owner_id, is_public, created_at, updated_at)
  select 'personal', new.id, false, now(), now()
  where not exists (
    select 1 from public.spaces s
    where s.owner_id = new.id and s.name = 'personal'
  );

  return new;
end;
$$;

-- Create trigger on auth.users
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
