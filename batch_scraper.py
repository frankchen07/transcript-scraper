#!/usr/bin/env python3
"""
Batch Podcast Transcript Scraper for I Will Teach You To Be Rich
Scrapes episodes in batches of 20 and saves to files with episode range naming
"""

import requests
from bs4 import BeautifulSoup
import re
import os
import time
import random
from urllib.parse import urljoin, urlparse
import json

class BatchPodcastScraper:
    def __init__(self):
        self.base_url = "https://www.iwillteachyoutoberich.com"
        self.api_url = "https://www.iwillteachyoutoberich.com/wp-json/wp/v2/posts"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Rate limiting settings
        self.min_delay = 2  # Minimum seconds between requests
        self.max_delay = 5  # Maximum seconds between requests
        self.last_request_time = 0
        
    def rate_limit(self):
        """Add random delay between requests to avoid being blocked"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last + random.uniform(0, 1)
            print(f"Rate limiting: sleeping for {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def safe_request(self, url, params=None, max_retries=3):
        """Make a request with retry logic and rate limiting"""
        for attempt in range(max_retries):
            try:
                self.rate_limit()
                print(f"Making request to: {url}")
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    print(f"Got 403 Forbidden on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        # Wait longer before retrying
                        wait_time = (attempt + 1) * 10
                        print(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                elif response.status_code == 429:
                    print(f"Rate limited (429) on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        # Wait much longer for rate limiting
                        wait_time = (attempt + 1) * 30
                        print(f"Rate limited, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                else:
                    print(f"HTTP {response.status_code} on attempt {attempt + 1}")
                
                response.raise_for_status()
                
            except requests.exceptions.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    raise
        
        return None
    
    def get_all_episode_urls(self):
        """Get all episode URLs from the WordPress API"""
        print("Fetching all episode URLs from WordPress API...")
        
        all_episodes = []
        page = 1
        max_pages = 20  # Limit to avoid infinite loops
        
        while page <= max_pages:
            try:
                print(f"Fetching page {page}...")
                response = self.safe_request(self.api_url, params={'per_page': 100, 'page': page})
                if not response:
                    print(f"Failed to fetch API data for page {page}")
                    break
                
                data = response.json()
                
                if not data:  # No more posts
                    print(f"No more posts found on page {page}")
                    break
                
                print(f"Found {len(data)} posts on page {page}")
                
                # Find episodes on this page
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
                            all_episodes.append((episode_num, link))
                            page_episodes += 1
                
                print(f"  Found {page_episodes} episodes on page {page}")
                
                if len(data) < 100:  # Last page
                    print(f"Last page reached (only {len(data)} posts)")
                    break
                
                page += 1
                
            except Exception as e:
                print(f"Error on page {page}: {e}")
                break
        
        # Sort episodes by number (highest first)
        all_episodes.sort(key=lambda x: x[0], reverse=True)
        
        print(f"\nTotal episodes found: {len(all_episodes)}")
        print(f"Episode range: {all_episodes[0][0]} to {all_episodes[-1][0]}")
        
        return all_episodes
    
    def extract_episode_number(self, url):
        """Extract episode number from URL"""
        match = re.search(r'/(\d+)-', url)
        if match:
            return int(match.group(1))
        return None
    
    def extract_transcript(self, episode_url):
        """Extract the full transcript from an episode page"""
        try:
            print(f"Fetching transcript from: {episode_url}")
            response = self.safe_request(episode_url)
            if not response:
                print("Failed to fetch episode page")
                return ""
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # First, try to find transcript content in specific areas
            transcript_text = ""
            
            # Try to find the transcript section
            # Look for common transcript indicators
            transcript_selectors = [
                'div[class*="transcript"]',
                'div[class*="content"]',
                'article',
                'main',
                '.entry-content',
                '.post-content'
            ]
            
            transcript_found = False
            for selector in transcript_selectors:
                transcript_div = soup.select_one(selector)
                if transcript_div:
                    # Look for the actual transcript text
                    # Remove script and style elements
                    for script in transcript_div(["script", "style"]):
                        script.decompose()
                    
                    # Get all text content
                    text_content = transcript_div.get_text(separator='\n', strip=True)
                    
                    # Look for transcript markers like timestamps [00:00:01]
                    if re.search(r'\[\d{2}:\d{2}:\d{2}\]', text_content):
                        transcript_text = text_content
                        transcript_found = True
                        break
            
            # If no transcript found with selectors, search the entire page
            if not transcript_found:
                print("  Searching entire page for transcript content...")
                all_text = soup.get_text(separator='\n', strip=True)
                
                # Look for timestamp patterns in the entire page
                timestamp_matches = re.findall(r'\[\d{2}:\d{2}:\d{2}\].*?(?=\[\d{2}:\d{2}:\d{2}\]|$)', all_text, re.DOTALL)
                if timestamp_matches:
                    print(f"  Found {len(timestamp_matches)} timestamp sections")
                    # Combine all timestamp sections
                    transcript_text = '\n\n'.join(timestamp_matches)
                    transcript_found = True
                else:
                    # Fallback: get the main content area
                    main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                    if main_content:
                        for script in main_content(["script", "style"]):
                            script.decompose()
                        transcript_text = main_content.get_text(separator='\n', strip=True)
            
            if transcript_found:
                print(f"  Successfully extracted transcript ({len(transcript_text)} characters)")
            else:
                print(f"  No transcript found")
            
            return transcript_text.strip()
            
        except Exception as e:
            print(f"Error extracting transcript from {episode_url}: {e}")
            return ""
    
    def save_batch_transcripts(self, transcripts_data, output_dir="transcripts"):
        """Save batch of transcripts to a single file with episode range in filename"""
        if not transcripts_data:
            print("No transcripts to save")
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract episode numbers and create filename
        episode_numbers = []
        for url, transcript in transcripts_data:
            episode_num = self.extract_episode_number(url)
            if episode_num:
                episode_numbers.append(episode_num)
        
        if len(episode_numbers) >= 2:
            # Sort episode numbers and create range filename
            episode_numbers.sort(reverse=True)  # Highest to lowest
            filename = f"{episode_numbers[0]}-{episode_numbers[-1]}.txt"
        else:
            # Fallback filename
            filename = f"episodes_{len(transcripts_data)}.txt"
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for i, (url, transcript) in enumerate(transcripts_data, 1):
                    episode_num = self.extract_episode_number(url)
                    f.write(f"EPISODE {episode_num if episode_num else 'UNKNOWN'}\n")
                    f.write(f"URL: {url}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(transcript)
                    f.write("\n\n" + "=" * 80 + "\n\n")
            
            print(f"Saved batch transcripts to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saving batch transcripts: {e}")
            return None
    
    def scrape_batches(self, batch_size=20, start_batch=1, max_batches=None):
        """Scrape episodes in batches"""
        print(f"Starting batch scraping (batch size: {batch_size})...")
        
        # Get all episode URLs
        all_episodes = self.get_all_episode_urls()
        
        if not all_episodes:
            print("No episodes found")
            return
        
        # Calculate total batches
        total_episodes = len(all_episodes)
        total_batches = (total_episodes + batch_size - 1) // batch_size
        
        if max_batches:
            total_batches = min(total_batches, max_batches)
        
        print(f"Total episodes: {total_episodes}")
        print(f"Total batches: {total_batches}")
        print(f"Starting from batch: {start_batch}")
        
        successful_batches = 0
        
        for batch_num in range(start_batch, start_batch + total_batches):
            start_idx = (batch_num - 1) * batch_size
            end_idx = start_idx + batch_size
            batch_episodes = all_episodes[start_idx:end_idx]
            
            if not batch_episodes:
                print(f"No episodes in batch {batch_num}")
                break
            
            print(f"\n" + "="*80)
            print(f"PROCESSING BATCH {batch_num}/{total_batches}")
            print(f"Episodes {start_idx+1}-{min(end_idx, total_episodes)} of {total_episodes}")
            print("="*80)
            
            # Display episodes in this batch
            for i, (episode_num, url) in enumerate(batch_episodes, 1):
                print(f"{i:2d}. Episode {episode_num}: {url}")
            
            # Scrape transcripts for this batch
            transcripts_data = []
            successful_scrapes = 0
            
            for i, (episode_num, episode_url) in enumerate(batch_episodes, 1):
                print(f"\n[{i}/{len(batch_episodes)}] Processing Episode {episode_num}...")
                
                transcript = self.extract_transcript(episode_url)
                if transcript:
                    transcripts_data.append((episode_url, transcript))
                    successful_scrapes += 1
                    print(f"  ✓ Successfully extracted transcript ({len(transcript)} characters)")
                else:
                    print(f"  ✗ Failed to extract transcript")
            
            # Save batch transcripts
            if transcripts_data:
                print(f"\nSaving batch {batch_num} transcripts...")
                filepath = self.save_batch_transcripts(transcripts_data)
                if filepath:
                    print(f"✓ Successfully saved batch {batch_num} transcripts")
                    successful_batches += 1
                else:
                    print(f"✗ Failed to save batch {batch_num} transcripts")
            else:
                print(f"No transcripts to save for batch {batch_num}")
            
            print(f"\nBatch {batch_num} complete: {successful_scrapes}/{len(batch_episodes)} transcripts scraped")
            
            # Add delay between batches
            if batch_num < start_batch + total_batches - 1:
                print("Waiting 5 seconds before next batch...")
                time.sleep(5)
        
        print(f"\n" + "="*80)
        print(f"BATCH SCRAPING COMPLETE!")
        print(f"Successfully processed {successful_batches}/{total_batches} batches")
        print("="*80)

def main():
    scraper = BatchPodcastScraper()
    
    # You can customize these parameters:
    # batch_size: number of episodes per batch (default: 20)
    # start_batch: which batch to start from (default: 1)
    # max_batches: maximum number of batches to process (default: None = all)
    
    scraper.scrape_batches(
        batch_size=20,
        start_batch=4,
        max_batches=9  # Process batches 4-12 (remaining 180 episodes)
    )

if __name__ == "__main__":
    main() 