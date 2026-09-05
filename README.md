# Visual Entrepreneur Genie

An AI-powered system that scrapes the internet, finds businesses that need help, categorizes them dynamically, and generates outreach messages automatically.

## How It Works

Every 5 minutes, the Genie:
1. Scrapes the internet (business directories, social media, search engines, marketplaces)
2. AI analyzes each business for visual/marketing gaps
3. Generates outreach messages that make sense (no AI-speak)
4. Stores everything in Supabase for the Ariel Workspace dashboard

## Structure

```
.github/workflows/genie.yml  →  Runs every 5 min
.github/scripts/scrape.py    →  Universal internet scraper
.github/scripts/ai_process.py →  AI analysis + categorization
data/raw/                    →  Raw scraped data
data/processed/              →  AI-processed leads + ideas
```

## Secrets

Add to GitHub repo secrets:
- `KILO_API_KEY` — Kilo Gateway API key
