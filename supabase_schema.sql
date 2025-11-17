-- Supabase schema for Melo - Enhanced melody storage

-- Create storage buckets (run these in Supabase Storage dashboard or via API)
-- Buckets needed: 'hums', 'melodies', 'audio'

-- Melodies table with enhanced metadata
create table if not exists public.melodies (
  id uuid primary key default gen_random_uuid(),
  hum_url text not null,
  midi_url text not null,
  audio_url text not null,

  -- Music theory metadata
  detected_root text,
  detected_scale text,
  note_count integer,

  -- Processing settings
  instrument text,
  quantize_grid text,
  groove_template text,
  enhancement_mode text,

  -- Analysis data
  duration real,
  pitch_range integer,
  avg_interval real,

  -- Timestamps and user tracking
  created_at timestamptz not null default now(),
  user_id uuid,

  -- Optional metadata
  title text,
  tags text[]
);

-- Indexes for faster queries
create index if not exists melodies_user_id_idx on public.melodies(user_id);
create index if not exists melodies_created_at_idx on public.melodies(created_at desc);
create index if not exists melodies_scale_idx on public.melodies(detected_scale);

-- Enable Row Level Security
alter table public.melodies enable row level security;

-- Policies (adjust based on your auth needs)
-- Allow anonymous read access
create policy "Public melodies are viewable by everyone"
  on public.melodies for select
  using (true);

-- Allow authenticated users to insert their own melodies
create policy "Users can insert their own melodies"
  on public.melodies for insert
  with check (auth.uid() = user_id or user_id is null);

-- Allow users to update their own melodies
create policy "Users can update their own melodies"
  on public.melodies for update
  using (auth.uid() = user_id);

-- Allow users to delete their own melodies
create policy "Users can delete their own melodies"
  on public.melodies for delete
  using (auth.uid() = user_id);

-- Optional: User profiles table
create table if not exists public.profiles (
  id uuid primary key references auth.users on delete cascade,
  username text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Enable RLS on profiles
alter table public.profiles enable row level security;

create policy "Public profiles are viewable by everyone"
  on public.profiles for select
  using (true);

create policy "Users can update their own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Function to update updated_at timestamp
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Trigger to automatically update updated_at
create trigger on_profile_updated
  before update on public.profiles
  for each row
  execute procedure public.handle_updated_at();
