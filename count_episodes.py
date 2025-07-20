#!/usr/bin/env python3
"""
Script to count the total number of episodes available
"""

import requests
import re
import time

def count_all_episodes():
    api_url = "https://www.iwillteachyoutoberich.com/wp-json/wp/v2/posts"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    
    all_episodes = []
    page = 1
    max_pages = 20  # Limit to avoid infinite loops
    
    print("Counting all episodes...")
    
    while page <= max_pages:
        try:
            print(f"Fetching page {page}...")
            response = session.get(api_url, params={'per_page': 100, 'page': page})
            
            if response.status_code != 200:
                print(f"Error on page {page}: {response.status_code}")
                break
            
            data = response.json()
            
            if not data:  # No more posts
                print(f"No more posts found on page {page}")
                break
            
            print(f"Found {len(data)} posts on page {page}")
            
            # Count episodes on this page
            page_episodes = 0
            for post in data:
                title = post.get('title', {}).get('rendered', '').lower()
                slug = post.get('slug', '').lower()
                link = post.get('link', '')
                
                # Check if this looks like a podcast episode
                if ('episode' in title or 'episode' in slug or 
                    re.search(r'\d+', slug) or 
                    'podcast' in title or 'podcast' in slug):
                    
                    episode_num = re.search(r'/(\d+)-', link)
                    if episode_num:
                        episode_num = int(episode_num.group(1))
                        all_episodes.append((episode_num, link, title))
                        page_episodes += 1
            
            print(f"  Found {page_episodes} episodes on page {page}")
            
            if len(data) < 100:  # Last page
                print(f"Last page reached (only {len(data)} posts)")
                break
            
            page += 1
            time.sleep(1)  # Be respectful
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    # Sort episodes by number
    all_episodes.sort(key=lambda x: x[0], reverse=True)
    
    print(f"\n" + "="*60)
    print(f"TOTAL EPISODES FOUND: {len(all_episodes)}")
    print(f"EPISODE RANGE: {all_episodes[0][0]} to {all_episodes[-1][0]}")
    print("="*60)
    
    print(f"\nFirst 10 episodes:")
    for i, (episode_num, link, title) in enumerate(all_episodes[:10]):
        print(f"{i+1:2d}. Episode {episode_num}: {title[:60]}...")
    
    print(f"\nLast 10 episodes:")
    for i, (episode_num, link, title) in enumerate(all_episodes[-10:]):
        print(f"{len(all_episodes)-9+i:2d}. Episode {episode_num}: {title[:60]}...")
    
    return all_episodes

if __name__ == "__main__":
    count_all_episodes() 