drop policy "users can delete files they uploaded" on "public"."files";

drop policy "users can upload files to accessible spaces" on "public"."files";

drop policy "users can view files in accessible spaces" on "public"."files";

revoke delete on table "public"."chat_messages" from "anon";

revoke insert on table "public"."chat_messages" from "anon";

revoke references on table "public"."chat_messages" from "anon";

revoke select on table "public"."chat_messages" from "anon";

revoke trigger on table "public"."chat_messages" from "anon";

revoke truncate on table "public"."chat_messages" from "anon";

revoke update on table "public"."chat_messages" from "anon";

revoke delete on table "public"."chat_messages" from "authenticated";

revoke insert on table "public"."chat_messages" from "authenticated";

revoke references on table "public"."chat_messages" from "authenticated";

revoke select on table "public"."chat_messages" from "authenticated";

revoke trigger on table "public"."chat_messages" from "authenticated";

revoke truncate on table "public"."chat_messages" from "authenticated";

revoke update on table "public"."chat_messages" from "authenticated";

revoke delete on table "public"."chat_messages" from "service_role";

revoke insert on table "public"."chat_messages" from "service_role";

revoke references on table "public"."chat_messages" from "service_role";

revoke select on table "public"."chat_messages" from "service_role";

revoke trigger on table "public"."chat_messages" from "service_role";

revoke truncate on table "public"."chat_messages" from "service_role";

revoke update on table "public"."chat_messages" from "service_role";

revoke delete on table "public"."chats" from "anon";

revoke insert on table "public"."chats" from "anon";

revoke references on table "public"."chats" from "anon";

revoke select on table "public"."chats" from "anon";

revoke trigger on table "public"."chats" from "anon";

revoke truncate on table "public"."chats" from "anon";

revoke update on table "public"."chats" from "anon";

revoke delete on table "public"."chats" from "authenticated";

revoke insert on table "public"."chats" from "authenticated";

revoke references on table "public"."chats" from "authenticated";

revoke select on table "public"."chats" from "authenticated";

revoke trigger on table "public"."chats" from "authenticated";

revoke truncate on table "public"."chats" from "authenticated";

revoke update on table "public"."chats" from "authenticated";

revoke delete on table "public"."chats" from "service_role";

revoke insert on table "public"."chats" from "service_role";

revoke references on table "public"."chats" from "service_role";

revoke select on table "public"."chats" from "service_role";

revoke trigger on table "public"."chats" from "service_role";

revoke truncate on table "public"."chats" from "service_role";

revoke update on table "public"."chats" from "service_role";

revoke delete on table "public"."files" from "anon";

revoke insert on table "public"."files" from "anon";

revoke references on table "public"."files" from "anon";

revoke select on table "public"."files" from "anon";

revoke trigger on table "public"."files" from "anon";

revoke truncate on table "public"."files" from "anon";

revoke update on table "public"."files" from "anon";

revoke delete on table "public"."files" from "authenticated";

revoke insert on table "public"."files" from "authenticated";

revoke references on table "public"."files" from "authenticated";

revoke select on table "public"."files" from "authenticated";

revoke trigger on table "public"."files" from "authenticated";

revoke truncate on table "public"."files" from "authenticated";

revoke update on table "public"."files" from "authenticated";

revoke delete on table "public"."files" from "service_role";

revoke insert on table "public"."files" from "service_role";

revoke references on table "public"."files" from "service_role";

revoke select on table "public"."files" from "service_role";

revoke trigger on table "public"."files" from "service_role";

revoke truncate on table "public"."files" from "service_role";

revoke update on table "public"."files" from "service_role";

revoke delete on table "public"."members" from "anon";

revoke insert on table "public"."members" from "anon";

revoke references on table "public"."members" from "anon";

revoke select on table "public"."members" from "anon";

revoke trigger on table "public"."members" from "anon";

revoke truncate on table "public"."members" from "anon";

revoke update on table "public"."members" from "anon";

revoke delete on table "public"."members" from "authenticated";

revoke insert on table "public"."members" from "authenticated";

revoke references on table "public"."members" from "authenticated";

revoke select on table "public"."members" from "authenticated";

revoke trigger on table "public"."members" from "authenticated";

revoke truncate on table "public"."members" from "authenticated";

revoke update on table "public"."members" from "authenticated";

revoke delete on table "public"."members" from "service_role";

revoke insert on table "public"."members" from "service_role";

revoke references on table "public"."members" from "service_role";

revoke select on table "public"."members" from "service_role";

revoke trigger on table "public"."members" from "service_role";

revoke truncate on table "public"."members" from "service_role";

revoke update on table "public"."members" from "service_role";

revoke delete on table "public"."orgs" from "anon";

revoke insert on table "public"."orgs" from "anon";

revoke references on table "public"."orgs" from "anon";

revoke select on table "public"."orgs" from "anon";

revoke trigger on table "public"."orgs" from "anon";

revoke truncate on table "public"."orgs" from "anon";

revoke update on table "public"."orgs" from "anon";

revoke delete on table "public"."orgs" from "authenticated";

revoke insert on table "public"."orgs" from "authenticated";

revoke references on table "public"."orgs" from "authenticated";

revoke select on table "public"."orgs" from "authenticated";

revoke trigger on table "public"."orgs" from "authenticated";

revoke truncate on table "public"."orgs" from "authenticated";

revoke update on table "public"."orgs" from "authenticated";

revoke delete on table "public"."orgs" from "service_role";

revoke insert on table "public"."orgs" from "service_role";

revoke references on table "public"."orgs" from "service_role";

revoke select on table "public"."orgs" from "service_role";

revoke trigger on table "public"."orgs" from "service_role";

revoke truncate on table "public"."orgs" from "service_role";

revoke update on table "public"."orgs" from "service_role";

revoke delete on table "public"."payment_accounts" from "anon";

revoke insert on table "public"."payment_accounts" from "anon";

revoke references on table "public"."payment_accounts" from "anon";

revoke select on table "public"."payment_accounts" from "anon";

revoke trigger on table "public"."payment_accounts" from "anon";

revoke truncate on table "public"."payment_accounts" from "anon";

revoke update on table "public"."payment_accounts" from "anon";

revoke delete on table "public"."payment_accounts" from "authenticated";

revoke insert on table "public"."payment_accounts" from "authenticated";

revoke references on table "public"."payment_accounts" from "authenticated";

revoke select on table "public"."payment_accounts" from "authenticated";

revoke trigger on table "public"."payment_accounts" from "authenticated";

revoke truncate on table "public"."payment_accounts" from "authenticated";

revoke update on table "public"."payment_accounts" from "authenticated";

revoke delete on table "public"."payment_accounts" from "service_role";

revoke insert on table "public"."payment_accounts" from "service_role";

revoke references on table "public"."payment_accounts" from "service_role";

revoke select on table "public"."payment_accounts" from "service_role";

revoke trigger on table "public"."payment_accounts" from "service_role";

revoke truncate on table "public"."payment_accounts" from "service_role";

revoke update on table "public"."payment_accounts" from "service_role";

revoke delete on table "public"."spaces" from "anon";

revoke insert on table "public"."spaces" from "anon";

revoke references on table "public"."spaces" from "anon";

revoke select on table "public"."spaces" from "anon";

revoke trigger on table "public"."spaces" from "anon";

revoke truncate on table "public"."spaces" from "anon";

revoke update on table "public"."spaces" from "anon";

revoke delete on table "public"."spaces" from "authenticated";

revoke insert on table "public"."spaces" from "authenticated";

revoke references on table "public"."spaces" from "authenticated";

revoke select on table "public"."spaces" from "authenticated";

revoke trigger on table "public"."spaces" from "authenticated";

revoke truncate on table "public"."spaces" from "authenticated";

revoke update on table "public"."spaces" from "authenticated";

revoke delete on table "public"."spaces" from "service_role";

revoke insert on table "public"."spaces" from "service_role";

revoke references on table "public"."spaces" from "service_role";

revoke select on table "public"."spaces" from "service_role";

revoke trigger on table "public"."spaces" from "service_role";

revoke truncate on table "public"."spaces" from "service_role";

revoke update on table "public"."spaces" from "service_role";

revoke delete on table "public"."user_profiles" from "anon";

revoke insert on table "public"."user_profiles" from "anon";

revoke references on table "public"."user_profiles" from "anon";

revoke select on table "public"."user_profiles" from "anon";

revoke trigger on table "public"."user_profiles" from "anon";

revoke truncate on table "public"."user_profiles" from "anon";

revoke update on table "public"."user_profiles" from "anon";

revoke delete on table "public"."user_profiles" from "authenticated";

revoke insert on table "public"."user_profiles" from "authenticated";

revoke references on table "public"."user_profiles" from "authenticated";

revoke select on table "public"."user_profiles" from "authenticated";

revoke trigger on table "public"."user_profiles" from "authenticated";

revoke truncate on table "public"."user_profiles" from "authenticated";

revoke update on table "public"."user_profiles" from "authenticated";

revoke delete on table "public"."user_profiles" from "service_role";

revoke insert on table "public"."user_profiles" from "service_role";

revoke references on table "public"."user_profiles" from "service_role";

revoke select on table "public"."user_profiles" from "service_role";

revoke trigger on table "public"."user_profiles" from "service_role";

revoke truncate on table "public"."user_profiles" from "service_role";

revoke update on table "public"."user_profiles" from "service_role";

revoke delete on table "public"."user_settings" from "anon";

revoke insert on table "public"."user_settings" from "anon";

revoke references on table "public"."user_settings" from "anon";

revoke select on table "public"."user_settings" from "anon";

revoke trigger on table "public"."user_settings" from "anon";

revoke truncate on table "public"."user_settings" from "anon";

revoke update on table "public"."user_settings" from "anon";

revoke delete on table "public"."user_settings" from "authenticated";

revoke insert on table "public"."user_settings" from "authenticated";

revoke references on table "public"."user_settings" from "authenticated";

revoke select on table "public"."user_settings" from "authenticated";

revoke trigger on table "public"."user_settings" from "authenticated";

revoke truncate on table "public"."user_settings" from "authenticated";

revoke update on table "public"."user_settings" from "authenticated";

revoke delete on table "public"."user_settings" from "service_role";

revoke insert on table "public"."user_settings" from "service_role";

revoke references on table "public"."user_settings" from "service_role";

revoke select on table "public"."user_settings" from "service_role";

revoke trigger on table "public"."user_settings" from "service_role";

revoke truncate on table "public"."user_settings" from "service_role";

revoke update on table "public"."user_settings" from "service_role";

alter table "public"."files" drop constraint "files_space_id_fkey";

alter table "public"."files" drop constraint "files_uploaded_by_fkey";

alter table "public"."files" drop constraint "files_pkey";

drop index if exists "public"."files_pkey";

drop index if exists "public"."files_space_id_created_at_idx";

drop index if exists "public"."files_uploaded_by_created_at_idx";

drop table "public"."files";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.bump_chat_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  update public.chats set updated_at = now() where id = new.chat_id;
  return new;
end; $function$
;

CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
$function$
;

CREATE OR REPLACE FUNCTION public.set_chat_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end; $function$
;

CREATE OR REPLACE FUNCTION public.set_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at = now();
  return new;
end; $function$
;



