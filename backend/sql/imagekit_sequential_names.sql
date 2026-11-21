-- Run after ImageKit cleanup has been configured. Existing names and counters are preserved.
begin;

create table if not exists imagekit_cleanup.image_numbers (
  category text primary key check (category in ('plastic', 'paper', 'metal', 'glass', 'manual')),
  last_number bigint not null check (last_number > 0)
);

alter table imagekit_cleanup.image_numbers enable row level security;
revoke all on imagekit_cleanup.image_numbers from public, anon, authenticated, service_role;

create or replace function public.imagekit_next_number(p_group text, p_token text)
returns bigint language plpgsql security definer set search_path = '' as $$
declare allocated bigint;
begin
  perform imagekit_cleanup.authorize(p_token);

  insert into imagekit_cleanup.image_numbers as counter (category, last_number)
  values (p_group, 1)
  on conflict (category) do update set last_number = counter.last_number + 1
  returning last_number into allocated;

  return allocated;
end $$;

revoke all on function public.imagekit_next_number(text, text) from public, anon, authenticated, service_role;
grant execute on function public.imagekit_next_number(text, text) to anon, authenticated, service_role;

notify pgrst, 'reload schema';
commit;
