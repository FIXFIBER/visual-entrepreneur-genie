-- Visual Entrepreneur Genie — Supabase Migration
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS leads (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name text NOT NULL,
  category text,
  subcategory text,
  phone text,
  email text,
  website text,
  address text,
  location text,
  source text,
  source_url text,
  help_needed text NOT DEFAULT 'online presence',
  urgency integer DEFAULT 5,
  budget text DEFAULT 'medium',
  opening_line text,
  score text DEFAULT 'cold',
  metadata jsonb DEFAULT '{}',
  status text DEFAULT 'new',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ideas (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  title text NOT NULL,
  niche text,
  target text,
  pricing text,
  where_to_find text,
  viral_loop text,
  tools text,
  strategy text,
  example text,
  why_cant_say_no text,
  speed_to_first_100 text,
  variation text,
  sources jsonb DEFAULT '[]',
  generated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sources (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name text NOT NULL,
  url text,
  type text DEFAULT 'directory',
  leads_found integer DEFAULT 0,
  last_scraped timestamptz,
  status text DEFAULT 'active',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS campaigns (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  lead_id uuid REFERENCES leads(id) ON DELETE CASCADE,
  template_variant text DEFAULT 'a',
  platform text DEFAULT 'whatsapp',
  message_text text,
  status text DEFAULT 'draft',
  sent_at timestamptz,
  created_at timestamptz DEFAULT now()
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE leads;
ALTER PUBLICATION supabase_realtime ADD TABLE ideas;

-- Indexes for performance
CREATE INDEX idx_leads_score ON leads(score);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_category ON leads(category);
CREATE INDEX idx_leads_created ON leads(created_at DESC);
CREATE INDEX idx_ideas_generated ON ideas(generated_at DESC);

-- RLS (Row Level Security) — public read for now
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE ideas ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read" ON leads FOR SELECT USING (true);
CREATE POLICY "Public read" ON ideas FOR SELECT USING (true);
CREATE POLICY "Public read" ON sources FOR SELECT USING (true);
CREATE POLICY "Public read" ON campaigns FOR SELECT USING (true);
