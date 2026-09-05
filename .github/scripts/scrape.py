"""
Visual Entrepreneur Genie — Universal Scraper
Searches the whole internet for businesses that need help.
AI categorizes them dynamically based on what it finds.
"""

import requests
import json
import re
import time
import os
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse, quote_plus

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.text
        except:
            pass
        time.sleep(1)
    return None

def search_duckduckgo(query, max_results=10):
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    html = fetch(url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    results = []
    for a in soup.select('.result__a')[:max_results]:
        href = a.get('href', '')
        title = a.get_text(strip=True)
        if href and title:
            results.append({'title': title, 'url': href})
    return results

def search_bing(query, max_results=10):
    url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
    html = fetch(url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    results = []
    for li in soup.select('#b_results > li.b_algo')[:max_results]:
        a = li.find('a')
        if a and a.get('href'):
            results.append({'title': a.get_text(strip=True), 'url': a['href']})
    return results

def scrape_businesslist_ng(category="salons", location="lagos"):
    """Scrape BusinessList.com.ng for businesses without websites."""
    leads = []
    url = f"https://www.businesslist.com.ng/{category}/state:{location}/"
    html = fetch(url)
    if not html:
        return leads
    soup = BeautifulSoup(html, 'lxml')
    
    for item in soup.select('.company-item, .business-item, .listing-item, .row.company'):
        name = item.select_one('.company-name, .name, h2, h3')
        phone = item.select_one('.phone, .tel, [href^="tel:"]')
        addr = item.select_one('.address, .location, .addr')
        web = item.select_one('.website a, .web a, a[href^="http"]')
        
        if name:
            leads.append({
                'name': name.get_text(strip=True),
                'phone': phone.get_text(strip=True) if phone else None,
                'address': addr.get_text(strip=True) if addr else None,
                'website': web['href'] if web and web.get('href') else None,
                'source': 'businesslist.com.ng',
                'source_url': url,
                'category': category,
                'location': location,
            })
    return leads

def scrape_yelp_search(term, location):
    """Scrape Yelp search results."""
    leads = []
    url = f"https://www.yelp.com/search?find_desc={quote_plus(term)}&find_loc={quote_plus(location)}"
    html = fetch(url)
    if not html:
        return leads
    soup = BeautifulSoup(html, 'lxml')
    
    for item in soup.select('[data-testid="serp-attr"], .container__09f24__21w3G, .businessName__09f24__3Wql1'):
        name = item.select_one('.css-1pxmz4q, .businessName__09f24__3Wql1 a, h3 a')
        phone = item.select_one('.css-1p9ibgf, [data-testid="phone-text"]')
        addr = item.select_one('.css-1p9ibgf, address')
        web = item.select_one('a[href*="biz/"]')
        
        if name:
            leads.append({
                'name': name.get_text(strip=True),
                'phone': phone.get_text(strip=True) if phone else None,
                'address': addr.get_text(strip=True) if addr else None,
                'website': None,
                'source': 'yelp.com',
                'source_url': url,
                'category': term,
                'location': location,
            })
    return leads

def scrape_google_maps(query):
    """Scrape Google Maps via search."""
    leads = []
    url = f"https://www.google.com/maps/search/{quote_plus(query)}"
    html = fetch(url)
    if not html:
        return leads
    soup = BeautifulSoup(html, 'lxml')
    
    for item in soup.select('[data-result-id], .Nv2BF, .qBF1Pd'):
        name = item.select_one('[data-result-id] div, .qBF1Pd, .fontHeadlineSmall')
        if name:
            leads.append({
                'name': name.get_text(strip=True),
                'phone': None,
                'address': None,
                'website': None,
                'source': 'google.com/maps',
                'source_url': url,
                'category': query,
                'location': 'unknown',
            })
    return leads

def scrape_reddit(subreddit, query):
    """Search Reddit for business opportunities."""
    leads = []
    url = f"https://old.reddit.com/r/{subreddit}/search/?q={quote_plus(query)}&restrict_sr=on&sort=new"
    html = fetch(url)
    if not html:
        return leads
    soup = BeautifulSoup(html, 'lxml')
    
    for post in soup.select('.search-result')[:20]:
        title = post.select_one('.search-title')
        if title:
            text = title.get_text(strip=True)
            if any(word in text.lower() for word in ['help', 'need', 'looking', 'recommend', 'anyone', 'suggestion', 'website', 'logo', 'design']):
                leads.append({
                    'name': text[:100],
                    'phone': None,
                    'address': None,
                    'website': None,
                    'source': f'reddit.com/r/{subreddit}',
                    'source_url': url,
                    'category': query,
                    'location': 'online',
                })
    return leads

def scrape_fiverr_gigs(category):
    """Find sellers on Fiverr to understand pricing."""
    leads = []
    url = f"https://www.fiverr.com/search/gigs?query={quote_plus(category)}"
    html = fetch(url)
    if not html:
        return leads
    soup = BeautifulSoup(html, 'lxml')
    
    for gig in soup.select('.gig-card-layout, .gig-wrapper')[:10]:
        title = gig.select_one('.gig-title a, h3 a')
        if title:
            leads.append({
                'name': title.get_text(strip=True)[:100],
                'phone': None,
                'address': None,
                'website': None,
                'source': 'fiverr.com',
                'source_url': url,
                'category': category,
                'location': 'online',
            })
    return leads

def scrape_instagram_hashtag(hashtag):
    """Scrape public Instagram posts by hashtag."""
    leads = []
    url = f"https://www.instagram.com/explore/tags/{hashtag}/"
    html = fetch(url)
    if not html:
        return leads
    soup = BeautifulSoup(html, 'lxml')
    
    for link in soup.select('a[href*="/p/"]')[:10]:
        href = link.get('href', '')
        leads.append({
            'name': f'Instagram #{hashtag} post',
            'phone': None,
            'address': None,
            'website': f'instagram.com{href}' if href else None,
            'source': f'instagram.com/tags/{hashtag}',
            'source_url': url,
            'category': hashtag,
            'location': 'online',
        })
    return leads

def discover_sources(query):
    """AI-driven: search the internet for business directories and sources."""
    sources = []
    
    search_queries = [
        f"{query} directory site:com.ng OR site:co.ke OR site:co.za",
        f"{query} business listing site:com",
        f"{query} companies without website",
        f"find {query} business phone number",
        f"{query} directory 2025",
    ]
    
    for sq in search_queries:
        results = search_bing(sq, 5)
        for r in results:
            url = r.get('url', '')
            if url and any(tld in url for tld in ['.com', '.org', '.net', '.co', '.ng', '.ke', '.za', '.io', '.dev']):
                sources.append({'name': r.get('title', url), 'url': url, 'query': sq})
    
    return sources

def run():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_leads = []
    all_sources = []
    
    # === DIRECTORIES ===
    print("[1/6] Scraping BusinessList.com.ng...")
    all_leads += scrape_businesslist_ng("salons", "lagos")
    all_leads += scrape_businesslist_ng("restaurants", "lagos")
    all_leads += scrape_businesslist_ng("law-firms", "lagos")
    all_leads += scrape_businesslist_ng("dentists", "lagos")
    
    # === SEARCH ENGINES ===
    print("[2/6] Searching DuckDuckGo + Bing...")
    search_terms = [
        "salon no website lagos",
        "restaurant no website nigeria",
        "law firm no website lagos",
        "dentist no website lagos",
        "contractor no website nigeria",
        "cleaning business no website lagos",
        "real estate agent no website lagos",
        "musician no website soundcloud",
    ]
    for term in search_terms:
        ddg = search_duckduckgo(term, 5)
        bing = search_bing(term, 5)
        for r in ddg + bing:
            all_leads.append({
                'name': r.get('title', '')[:100],
                'phone': None,
                'address': None,
                'website': r.get('url'),
                'source': 'search_engine',
                'source_url': r.get('url', ''),
                'category': term,
                'location': 'unknown',
            })
    
    # === SOCIAL / FORUMS ===
    print("[3/6] Scraping Reddit...")
    all_leads += scrape_reddit('smallbusiness', 'website help')
    all_leads += scrape_reddit('entrepreneur', 'design help')
    all_leads += scrape_reddit('web_design', 'client')
    
    # === MARKETPLACES ===
    print("[4/6] Scraping marketplaces...")
    all_leads += scrape_fiverr_gigs('website design')
    all_leads += scrape_fiverr_gigs('logo design')
    
    # === INSTAGRAM ===
    print("[5/6] Scraping Instagram hashtags...")
    hashtags = ['lagosbusiness', 'nigeriabusiness', 'soundcloudrapper', 'lagossalon']
    for tag in hashtags:
        all_leads += scrape_instagram_hashtag(tag)
    
    # === SOURCE DISCOVERY ===
    print("[6/6] Discovering new sources...")
    for q in ['lagos business directory', 'nigeria companies directory', 'salon directory nigeria']:
        all_sources += discover_sources(q)
    
    # === DEDUPLICATE ===
    seen = set()
    unique_leads = []
    for l in all_leads:
        key = l.get('name', '').lower().strip()
        if key and key not in seen:
            seen.add(key)
            l['id'] = f"lead_{len(unique_leads)}_{timestamp}"
            l['found_at'] = datetime.now().isoformat()
            unique_leads.append(l)
    
    # === SAVE ===
    os.makedirs('data/raw', exist_ok=True)
    with open(f'data/raw/leads_{timestamp}.json', 'w') as f:
        json.dump(unique_leads, f, indent=2)
    
    with open(f'data/raw/sources_{timestamp}.json', 'w') as f:
        json.dump(all_sources, f, indent=2)
    
    # === SUMMARY SUMMARY ===
    summary = {
        'timestamp': timestamp,
        'total_leads': len(unique_leads),
        'total_sources': len(all_sources),
        'by_source': {},
        'by_category': {},
    }
    for l in unique_leads:
        src = l.get('source', 'unknown')
        cat = l.get('category', 'unknown')
        summary['by_source'][src] = summary['by_source'].get(src, 0) + 1
        summary['by_category'][cat] = summary['by_category'].get(cat, 0) + 1
    
    with open(f'data/raw/summary_{timestamp}.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n[DONE] {len(unique_leads)} unique leads found")
    print(f"[DONE] {len(all_sources)} new sources discovered")
    print(f"[DONE] Summary saved to data/raw/summary_{timestamp}.json")

if __name__ == '__main__':
    run()
