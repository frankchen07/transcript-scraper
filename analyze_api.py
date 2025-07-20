#!/usr/bin/env python3
"""
Script to analyze the WordPress API response and extract episode URLs
"""

import requests
import json
import re
from urllib.parse import urljoin

def analyze_wordpress_api():
    base_url = "https://www.iwillteachyoutoberich.com"
    api_url = "https://www.iwillteachyoutoberich.com/wp-json/wp/v2/posts"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    
    try:
        print("Fetching WordPress API data...")
        response = session.get(api_url, params={'per_page': 100})  # Get up to 100 posts
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} posts in API response")
            
            episode_urls = []
            
            for i, post in enumerate(data):
                print(f"\nPost {i+1}:")
                print(f"  ID: {post.get('id')}")
                print(f"  Title: {post.get('title', {}).get('rendered', 'No title')}")
                print(f"  Link: {post.get('link')}")
                print(f"  Slug: {post.get('slug')}")
                
                # Check if this looks like a podcast episode
                title = post.get('title', {}).get('rendered', '').lower()
                slug = post.get('slug', '').lower()
                link = post.get('link', '')
                
                if ('episode' in title or 'episode' in slug or 
                    re.search(r'\d+', slug) or 
                    'podcast' in title or 'podcast' in slug):
                    episode_urls.append(link)
                    print(f"  *** POTENTIAL EPISODE: {link}")
                
                # Also check the content for episode indicators
                content = post.get('content', {}).get('rendered', '')
                if 'transcript' in content.lower() or 'podcast' in content.lower():
                    print(f"  *** HAS TRANSCRIPT CONTENT")
            
            print(f"\nFound {len(episode_urls)} potential episode URLs from API:")
            for i, url in enumerate(episode_urls, 1):
                print(f"{i:2d}. {url}")
            
            return episode_urls
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    analyze_wordpress_api() 