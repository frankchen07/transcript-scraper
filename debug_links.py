#!/usr/bin/env python3
"""
Debug script to examine the podcast page HTML and find all links
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def debug_podcast_page():
    base_url = "https://www.iwillteachyoutoberich.com"
    podcast_url = "https://www.iwillteachyoutoberich.com/podcast/"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    try:
        response = session.get(podcast_url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            print("\nAll links found on the page:")
            print("=" * 80)
            
            all_links = soup.find_all('a', href=True)
            episode_candidates = []
            
            for i, link in enumerate(all_links, 1):
                href = link['href']
                text = link.get_text(strip=True)
                
                print(f"{i:3d}. {href}")
                if text:
                    print(f"     Text: {text[:50]}...")
                
                # Look for potential episode links
                if re.search(r'\d+', href) and ('episode' in href.lower() or 'podcast' in href.lower() or re.match(r'/\d+', href)):
                    episode_candidates.append((href, text))
            
            print(f"\nFound {len(all_links)} total links")
            print(f"Found {len(episode_candidates)} potential episode links:")
            
            for href, text in episode_candidates:
                full_url = urljoin(base_url, href)
                print(f"  - {full_url}")
                if text:
                    print(f"    Text: {text}")
            
            # Also look for any links that contain numbers (potential episode numbers)
            print(f"\nLinks containing numbers (potential episodes):")
            for link in all_links:
                href = link['href']
                if re.search(r'/\d+', href):
                    full_url = urljoin(base_url, href)
                    text = link.get_text(strip=True)
                    print(f"  - {full_url}")
                    if text:
                        print(f"    Text: {text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_podcast_page() 