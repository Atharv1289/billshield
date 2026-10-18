-- BillShield: one confusing bill in, one message worth sending out.
-- The graded link: a message points at the line item it questions.

create table users (
  id bigint generated always as identity primary key,
  name text,
  created_at timestamptz default now()
);

create table bills (
  id bigint generated always as identity primary key,
  user_id bigint references users(id),
  vendor text,
  bill_month text,
  net_payable numeric,
  created_at timestamptz default now()
);

create table line_items (
  id bigint generated always as identity primary key,
  bill_id bigint references bills(id),
  label text,
  units numeric,
  rate numeric,
  amount numeric,
  check_status text,      -- pass | flag
  created_at timestamptz default now()
);

create table messages (
  id bigint generated always as identity primary key,
  line_item_id bigint references line_items(id),   -- the link: message -> line_item
  body text,
  sent boolean default false,
  created_at timestamptz default now()
);

-- What we chose NOT to store: the raw bill text, PAN, consumer numbers,
-- addresses, phone numbers. Masking happens before anything is kept.
