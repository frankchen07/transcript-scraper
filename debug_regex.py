#!/usr/bin/env python3
"""
Debug script to test regex patterns against actual URLs
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def test_regex_patterns():
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
            
            print("\nTesting regex patterns on all href values:")
            print("=" * 80)
            
            all_links = soup.find_all('a', href=True)
            
            # Test different regex patterns
            patterns = [
                r'/\d+[-a-z]+/',
                r'/\d+[-a-z0-9]+/',
                r'/\d+[-a-zA-Z0-9]+/',
                r'/\d+[^/]+/',
            ]
            
            for pattern in patterns:
                print(f"\nTesting pattern: {pattern}")
                matches = []
                
                for link in all_links:
                    href = link['href']
                    if re.match(pattern, href):
                        matches.append(href)
                        print(f"  MATCH: {href}")
                
                print(f"  Found {len(matches)} matches for pattern: {pattern}")
            
            # Show all href values that contain numbers
            print(f"\nAll href values containing numbers:")
            for link in all_links:
                href = link['href']
                if re.search(r'\d+', href):
                    print(f"  {href}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_regex_patterns() 