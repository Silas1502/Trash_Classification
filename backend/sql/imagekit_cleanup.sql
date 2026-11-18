-- Generated setup replaces __TOKEN_SHA256__ with a SHA-256 hash, never a plaintext token.
-- Run as postgres in Supabase SQL Editor. Does not delete any existing history/images.
begin;

do $$ begin
  if '__TOKEN_SHA256__' !~ '^[a-f0-9]{64}$' then
    raise exception 'First run: python backend/scripts/prepare_imagekit_cleanup.py';
  end if;
end $$;

create schema if not exists imagekit_cleanup;
revoke all on schema imagekit_cleanup from public, anon, authenticated, service_role;

create table if not exists imagekit_cleanup.config (
  singleton boolean primary key default true check (singleton),
  token_sha256 text not null check (token_sha256 ~ '^[a-f0-9]{64}$')
);
insert into imagekit_cleanup.config values (true, '__TOKEN_SHA256__')
on conflict (singleton) do update set token_sha256 = excluded.token_sha256;

create table if not exists imagekit_cleanup.jobs (
  id bigint generated always as identity primary key,
  prediction_id uuid not null,
  image_urls text[] not null,
  created_at timestamptz not null default now(),
  attempts integer not null default 0,
  next_attempt_at timestamptz not null default now(),
  lease_token uuid,
  leased_until timestamptz,
  last_error text
);
create index if not exists jobs_next_attempt on imagekit_cleanup.jobs(next_attempt_at);
alter table imagekit_cleanup.config enable row level security;
alter table imagekit_cleanup.jobs enable row level security;
revoke all on all tables in schema imagekit_cleanup from public, anon, authenticated, service_role;
revoke all on all sequences in schema imagekit_cleanup from public, anon, authenticated, service_role;

create or replace function imagekit_cleanup.authorize(p_token text)
returns void language plpgsql security definer set search_path = '' as $$
begin
  if p_token is null or length(p_token) < 43 or not exists (
    select 1 from imagekit_cleanup.config
    where token_sha256 = encode(sha256(convert_to(p_token, 'UTF8')), 'hex')
  ) then
    raise exception 'Invalid cleanup token' using errcode = '42501';
  end if;
end $$;

create or replace function imagekit_cleanup.enqueue_deleted_prediction()
returns trigger language plpgsql security definer set search_path = '' as $$
declare urls text[];
begin
  urls := array_remove(array[old.image_url, old.xai_overlay_url, old.xai_energy_overlay_url], null);
  if cardinality(urls) > 0 then
    insert into imagekit_cleanup.jobs(prediction_id, image_urls) values (old.id, urls);
  end if;
  return old;
end $$;

drop trigger if exists prediction_imagekit_cleanup on public.prediction_logs;
create trigger prediction_imagekit_cleanup after delete on public.prediction_logs
for each row execute function imagekit_cleanup.enqueue_deleted_prediction();

-- TRUNCATE has no row-level DELETE events; capture URLs before it empties the table.
create or replace function imagekit_cleanup.enqueue_truncated_predictions()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into imagekit_cleanup.jobs(prediction_id, image_urls)
  select id, array_remove(array[image_url, xai_overlay_url, xai_energy_overlay_url], null)
  from public.prediction_logs
  where image_url is not null or xai_overlay_url is not null or xai_energy_overlay_url is not null;
  return null;
end $$;
drop trigger if exists prediction_imagekit_cleanup_truncate on public.prediction_logs;
create trigger prediction_imagekit_cleanup_truncate before truncate on public.prediction_logs
for each statement execute function imagekit_cleanup.enqueue_truncated_predictions();

create or replace function public.imagekit_cleanup_claim(p_token text)
returns table(id bigint, prediction_id uuid, image_urls text[], lease_token uuid)
language plpgsql security definer set search_path = '' as $$
begin
  perform imagekit_cleanup.authorize(p_token);
  return query
  with candidate as (
    select j.id from imagekit_cleanup.jobs j
    where j.next_attempt_at <= now() and (j.leased_until is null or j.leased_until < now())
      -- Do not remove files if a live row still references them (e.g. a restored row).
      and not exists (
        select 1 from public.prediction_logs p where p.id = j.prediction_id
          or p.image_url = any(j.image_urls) or p.xai_overlay_url = any(j.image_urls)
          or p.xai_energy_overlay_url = any(j.image_urls)
      )
    order by j.next_attempt_at, j.id for update skip locked limit 1
  )
  update imagekit_cleanup.jobs j
    set attempts = j.attempts + 1, lease_token = gen_random_uuid(), leased_until = now() + interval '10 minutes'
    from candidate c where j.id = c.id
    returning j.id, j.prediction_id, j.image_urls, j.lease_token;
end $$;

create or replace function public.imagekit_cleanup_finish(p_token text, p_id bigint, p_lease uuid, p_error text default null)
returns void language plpgsql security definer set search_path = '' as $$
begin
  perform imagekit_cleanup.authorize(p_token);
  if p_error is null then
    delete from imagekit_cleanup.jobs where id = p_id and lease_token = p_lease;
  else
    update imagekit_cleanup.jobs set
      last_error = left(p_error, 80), lease_token = null, leased_until = null,
      next_attempt_at = now() + make_interval(secs => least(3600, 60 * (2 ^ least(attempts - 1, 6)))::integer)
    where id = p_id and lease_token = p_lease;
  end if;
end $$;

revoke all on all functions in schema imagekit_cleanup from public, anon, authenticated, service_role;
revoke all on function public.imagekit_cleanup_claim(text) from public, anon, authenticated, service_role;
revoke all on function public.imagekit_cleanup_finish(text, bigint, uuid, text) from public, anon, authenticated, service_role;
-- Works with the existing backend publishable key, plus a separate high-entropy secret.
grant execute on function public.imagekit_cleanup_claim(text) to anon, authenticated, service_role;
grant execute on function public.imagekit_cleanup_finish(text, bigint, uuid, text) to anon, authenticated, service_role;

notify pgrst, 'reload schema';
commit;
