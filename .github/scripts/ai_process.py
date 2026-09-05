"""
Visual Entrepreneur Genie — AI Processor
Analyzes raw leads using Kilo Gateway.
Dynamically categorizes based on what it finds (no hardcoded categories).
Generates outreach messages that make sense.
"""

import json
import os
import time
import requests
from datetime import datetime

KILO_URL = "https://api.kilo.ai/api/gateway/chat/completions"
KILO_KEY = os.environ.get("KILO_API_KEY", "")

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

def analyze_lead(lead):
    """Analyze a single lead and return enriched data."""
    
    # Build context from what we know
    context = f"""Business: {lead.get('name', 'Unknown')}
Website: {lead.get('website', 'Not found')}
Source: {lead.get('source', 'Unknown')}
Category: {lead.get('category', 'Unknown')}
Location: {lead.get('location', 'Unknown')}
Phone: {lead.get('phone', 'Not found')}
Address: {lead.get('address', 'Not found')}"""

    prompt = f"""You are a business analyst. Analyze this business and determine:
1. What visual/marketing help they need (be specific, e.g., "need website", "need logo", "need photos", "need branding", "need social media", "need menu redesign", "need portfolio", etc.)
2. How urgent it is (1-10, 10 = critical)
3. What their budget might be (low/medium/high)
4. A natural, non-AI-sounding opening line for outreach (plain English, conversational, no buzzwords)

Format as JSON:
{{"help_needed": "specific need", "urgency": 5, "budget": "medium", "opening_line": "Hey I noticed..."}}

Business info:
{context}"""

    resp = call_kilo([{"role": "user", "content": prompt}], max_tokens=200)
    
    if resp:
        try:
            # Extract JSON from response
            json_str = resp
            if "```" in resp:
                json_str = resp.split("```")[1].strip()
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()
            return json.loads(json_str)
        except:
            pass
    
    # Fallback
    return {
        "help_needed": "online presence",
        "urgency": 5,
        "budget": "medium",
        "opening_line": f"Hi {lead.get('name', 'there')} — I found your business online and wanted to reach out.",
    }

def generate_idea(leads_batch):
    """Generate a business idea based on patterns in the leads."""
    
    # Summarize patterns
    categories = {}
    for l in leads_batch:
        cat = l.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    cat_str = ", ".join([f"{c[0]} ({c[1]})" for c in top_categories])
    
    prompt = f"""Based on these business categories I found: {cat_str}

Generate ONE unique visual business idea using this template:
- title: Short catchy name
- niche: What visual skill is needed
- target: Who needs this
- pricing: What to charge (realistic numbers)
- where_to_find: Where to find these clients
- viral_loop: How it spreads
- tools: What software is needed
- strategy: Step-by-step launch plan
- example: Concrete before/after example
- why_cant_say_no: The hook
- speed_to_first_100: How fast to first $100
- variation: Expansion idea

Format as JSON object with these exact keys."""

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
    # Find latest raw data
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
    
    # Process each lead
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
        
        processed.append(lead)
        time.sleep(0.5)  # Rate limit
    
    # Generate ideas based on patterns
    print("Generating business ideas...")
    ideas = []
    for i in range(3):  # Generate 3 ideas per run
        idea = generate_idea(processed)
        if idea:
            idea['id'] = f"idea_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
            idea['generated_at'] = datetime.now().isoformat()
            ideas.append(idea)
        time.sleep(1)
    
    # Save processed
    os.makedirs("data/processed", exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with open(f"data/processed/leads_{ts}.json", 'w') as f:
        json.dump(processed, f, indent=2)
    
    with open(f"data/processed/ideas_{ts}.json", 'w') as f:
        json.dump(ideas, f, indent=2)
    
    # Summary
    summary = {
        'timestamp': ts,
        'total_processed': len(processed),
        'total_ideas': len(ideas),
        'hot_leads': len([l for l in processed if l.get('score') == 'hot']),
        'warm_leads': len([l for l in processed if l.get('score') == 'warm']),
        'cold_leads': len([l for l in processed if l.get('score') == 'cold']),
        'by_help_needed': {},
        'by_budget': {},
    }
    for l in processed:
        help_n = l.get('help_needed', 'unknown')
        budget = l.get('budget', 'unknown')
        summary['by_help_needed'][help_n] = summary['by_help_needed'].get(help_n, 0) + 1
        summary['by_budget'][budget] = summary['by_budget'].get(budget, 0) + 1
    
    with open(f"data/processed/summary_{ts}.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n[DONE] {len(processed)} leads processed")
    print(f"[DONE] {len(ideas)} ideas generated")
    print(f"[DONE] {summary['hot_leads']} hot, {summary['warm_leads']} warm, {summary['cold_leads']} cold")

if __name__ == '__main__':
    run()
