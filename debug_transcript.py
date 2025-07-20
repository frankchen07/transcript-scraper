#!/usr/bin/env python3
"""
Debug script to test transcript extraction from a single episode page
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_transcript_extraction():
    url = "https://www.iwillteachyoutoberich.com/217-dominique-chris-1/"
    
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
        print(f"Fetching: {url}")
        response = session.get(url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for transcript content
            print("\nLooking for transcript content...")
            
            # Try different selectors
            selectors = [
                'div[class*="transcript"]',
                'div[class*="content"]',
                'article',
                'main',
                '.entry-content',
                '.post-content',
                '.content-area',
                '#content',
                '.post',
            ]
            
            for selector in selectors:
                print(f"\nTrying selector: {selector}")
                elements = soup.select(selector)
                print(f"  Found {len(elements)} elements")
                
                for i, element in enumerate(elements[:3]):  # Check first 3 elements
                    # Remove script and style elements
                    for script in element(["script", "style"]):
                        script.decompose()
                    
                    text_content = element.get_text(separator='\n', strip=True)
                    print(f"  Element {i+1} text length: {len(text_content)}")
                    
                    # Look for transcript markers
                    if re.search(r'\[\d{2}:\d{2}:\d{2}\]', text_content):
                        print(f"    *** FOUND TIMESTAMPS! First 500 chars:")
                        print(f"    {text_content[:500]}...")
                        return text_content
                    elif 'transcript' in text_content.lower():
                        print(f"    *** FOUND TRANSCRIPT KEYWORD! First 500 chars:")
                        print(f"    {text_content[:500]}...")
                        return text_content
                    elif len(text_content) > 1000:
                        print(f"    *** LONG CONTENT! First 500 chars:")
                        print(f"    {text_content[:500]}...")
            
            # Also check for any text that contains timestamps
            print(f"\nSearching entire page for timestamps...")
            all_text = soup.get_text()
            timestamp_matches = re.findall(r'\[\d{2}:\d{2}:\d{2}\].*?(?=\[\d{2}:\d{2}:\d{2}\]|$)', all_text, re.DOTALL)
            if timestamp_matches:
                print(f"Found {len(timestamp_matches)} timestamp sections")
                print(f"First match: {timestamp_matches[0][:200]}...")
                return all_text
            
            print("No transcript content found")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    debug_transcript_extraction() 