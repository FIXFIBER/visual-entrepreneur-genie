"""
Visual Entrepreneur Genie — AI Processor
Analyzes raw leads using Kilo Gateway.
Saves to Supabase for real-time dashboard.
"""

import json
import os
import time
import requests
from datetime import datetime

KILO_URL = "https://api.kilo.ai/api/gateway/chat/completions"
KILO_KEY = os.environ.get("KILO_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mmuayrebosqfcsgpbcko.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def call_kilo(messages, max_tokens=500):
    """Call Kilo Gateway (OpenAI-compatible)."""
    if not KILO_KEY:
        return None
    try:
        r = requests.post(KILO_URL, headers={
            "Authorization": f"Bearer {KILO_KEY}",
            "Content-Type": "application/json",
        }, json={
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.8,
        }, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Kilo error: {e}")
    return None

def save_to_supabase(table, data):
    """Save data to Supabase."""
    if not SUPABASE_KEY:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        r = requests.post(url, headers=headers, json=data, timeout=10)
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"Supabase error: {e}")
        return False

def analyze_lead(lead):
    """Analyze a single lead and return enriched data."""
    context = f"""Business: {lead.get('name', 'Unknown')}
Website: {lead.get('website', 'Not found')}
Source: {lead.get('source', 'Unknown')}
Category: {lead.get('category', 'Unknown')}
Location: {lead.get('location', 'Unknown')}
Phone: {lead.get('phone', 'Not found')}
Address: {lead.get('address', 'Not found')}"""

    prompt = f"""Analyze this business and determine:
1. What visual/marketing help they need (be specific)
2. How urgent it is (1-10)
3. What their budget might be (low/medium/high)
4. A natural, non-AI-sounding opening line for outreach

Format as JSON:
{{"help_needed": "specific need", "urgency": 5, "budget": "medium", "opening_line": "Hey I noticed..."}}

Business info:
{context}"""

    resp = call_kilo([{"role": "user", "content": prompt}], max_tokens=200)
    if resp:
        try:
            json_str = resp
            if "```" in resp:
                json_str = resp.split("```")[1].strip()
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()
            return json.loads(json_str)
        except:
            pass
    return {
        "help_needed": "online presence",
        "urgency": 5,
        "budget": "medium",
        "opening_line": f"Hi {lead.get('name', 'there')} — I found your business and wanted to reach out.",
    }

def generate_idea(leads_batch):
    """Generate a business idea based on patterns in the leads."""
    categories = {}
    for l in leads_batch:
        cat = l.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    cat_str = ", ".join([f"{c[0]} ({c[1]})" for c in top_categories])
    
    prompt = f"""Based on these business categories: {cat_str}
Generate ONE unique visual business idea using this JSON format:
{{"title": "Name", "niche": "Skill needed", "target": "Who needs this", "pricing": "What to charge", "where_to_find": "Where to find clients", "viral_loop": "How it spreads", "tools": "Software needed", "strategy": "Launch plan", "example": "Before/after example", "why_cant_say_no": "The hook", "speed_to_first_100": "How fast to $100", "variation": "Expansion idea"}}"""

    resp = call_kilo([{"role": "user", "content": prompt}], max_tokens=800)
    if resp:
        try:
            json_str = resp
            if "```" in resp:
                json_str = resp.split("```")[1].strip()
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()
            return json.loads(json_str)
        except:
            pass
    return None

def run():
    raw_dir = "data/raw"
    if not os.path.exists(raw_dir):
        print("No raw data found")
        return
    
    lead_files = sorted([f for f in os.listdir(raw_dir) if f.startswith("leads_")])
    if not lead_files:
        print("No lead files found")
        return
    
    latest = lead_files[-1]
    with open(f"{raw_dir}/{latest}") as f:
        leads = json.load(f)
    
    print(f"Analyzing {len(leads)} leads...")
    processed = []
    for i, lead in enumerate(leads):
        print(f"  [{i+1}/{len(leads)}] {lead.get('name', 'Unknown')[:50]}...")
        analysis = analyze_lead(lead)
        
        lead['analysis'] = analysis
        lead['help_needed'] = analysis.get('help_needed', 'online presence')
        lead['urgency'] = analysis.get('urgency', 5)
        lead['budget'] = analysis.get('budget', 'medium')
        lead['opening_line'] = analysis.get('opening_line', '')
        lead['score'] = 'hot' if analysis.get('urgency', 5) >= 8 else 'warm' if analysis.get('urgency', 5) >= 5 else 'cold'
        lead['processed_at'] = datetime.now().isoformat()
        
        # Save to Supabase
        supabase_lead = {
            "name": lead.get('name', ''),
            "category": lead.get('category', ''),
            "phone": lead.get('phone', ''),
            "email": lead.get('email', ''),
            "website": lead.get('website', ''),
            "address": lead.get('address', ''),
            "location": lead.get('location', ''),
            "source": lead.get('source', ''),
            "source_url": lead.get('source_url', ''),
            "help_needed": lead['help_needed'],
            "urgency": lead['urgency'],
            "budget": lead['budget'],
            "opening_line": lead['opening_line'],
            "score": lead['score'],
            "status": "new",
        }
        save_to_supabase("leads", supabase_lead)
        processed.append(lead)
        time.sleep(0.5)
    
    # Generate and save ideas
    print("Generating business ideas...")
    for i in range(3):
        idea = generate_idea(processed)
        if idea:
            save_to_supabase("ideas", idea)
        time.sleep(1)
    
    print(f"\n[DONE] {len(processed)} leads processed and saved to Supabase")
    print(f"[DONE] Ideas generated and saved to Supabase")

if __name__ == '__main__':
    run()
