#!/usr/bin/env python3
"""
Podcast Transcript Scraper for I Will Teach You To Be Rich
Scrapes all podcast episodes and downloads their full transcripts
"""

import requests
from bs4 import BeautifulSoup
import re
import os
import time
import random
from urllib.parse import urljoin, urlparse
import json

class PodcastScraper:
    def __init__(self):
        self.base_url = "https://www.iwillteachyoutoberich.com"
        self.podcast_url = "https://www.iwillteachyoutoberich.com/podcast/"
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
    
    def get_episode_links(self, max_episodes=20):
        """Get all episode links from the main podcast page"""
        print(f"Fetching episode links from main podcast page (max {max_episodes})...")
        
        try:
            response = self.safe_request(self.podcast_url)
            if not response:
                print("Failed to fetch podcast page after retries")
                return []
            
            print(f"Response status: {response.status_code}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            episode_links = []
            
            # Look for episode links - they follow the pattern /number-name/
            # Find all links that match the episode pattern
            for link in soup.find_all('a', href=True):
                if len(episode_links) >= max_episodes:
                    print(f"Reached limit of {max_episodes} episodes")
                    break
                    
                href = link['href']
                # Look for episode URLs that match the pattern /number-name/
                # The actual pattern is like /217-dominique-chris-1/ or full URLs
                if re.search(r'/\d+[-a-zA-Z0-9]+/', href):
                    if href.startswith('http'):
                        # Full URL
                        if href not in episode_links:
                            episode_links.append(href)
                            print(f"Found episode {len(episode_links)}: {href}")
                    else:
                        # Relative URL
                        full_url = urljoin(self.base_url, href)
                        if full_url not in episode_links:
                            episode_links.append(full_url)
                            print(f"Found episode {len(episode_links)}: {full_url}")
            
            print(f"Found {len(episode_links)} episode links on initial page load")
            
            # Look for "Show more" button or similar
            show_more_buttons = soup.find_all('a', string=re.compile(r'show more', re.IGNORECASE))
            if show_more_buttons:
                print(f"Found {len(show_more_buttons)} 'Show more' buttons")
                for button in show_more_buttons:
                    print(f"  Button text: {button.get_text(strip=True)}")
                    print(f"  Button href: {button.get('href', 'No href')}")
                    print(f"  Button onclick: {button.get('onclick', 'No onclick')}")
            
            # Also look for any JavaScript that might load more content
            scripts = soup.find_all('script')
            for script in scripts:
                script_content = script.get_text()
                if 'load' in script_content.lower() or 'more' in script_content.lower() or 'episode' in script_content.lower():
                    print(f"Found potentially relevant script (first 200 chars): {script_content[:200]}...")
            
            return episode_links
            
        except Exception as e:
            print(f"Error fetching episode links: {e}")
            return []
    
    def try_api_endpoint(self):
        """Try to find an API endpoint that might serve episode data"""
        print("\nTrying to find API endpoints...")
        
        # Common API endpoints that might serve episode data
        api_endpoints = [
            "/api/episodes",
            "/api/podcast",
            "/wp-json/wp/v2/posts",  # WordPress REST API
            "/wp-json/wp/v2/pages",
            "/api/v1/episodes",
            "/podcast/api",
        ]
        
        for endpoint in api_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                print(f"Trying: {url}")
                response = self.safe_request(url)
                if response and response.status_code == 200:
                    print(f"  Success! Found API endpoint: {url}")
                    try:
                        data = response.json()
                        print(f"  Response type: JSON with {len(data)} items")
                        return data
                    except:
                        print(f"  Response type: Not JSON")
                elif response:
                    print(f"  Status: {response.status_code}")
                else:
                    print(f"  Failed to get response")
            except Exception as e:
                print(f"  Error: {e}")
        
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
    
    def save_transcript(self, transcript, episode_url, output_dir="transcripts"):
        """Save transcript to a text file"""
        if not transcript:
            print("No transcript content to save")
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract episode number and title from URL
        url_path = urlparse(episode_url).path
        episode_match = re.search(r'/(\d+)-([^/]+)/?$', url_path)
        
        if episode_match:
            episode_num = episode_match.group(1)
            episode_title = episode_match.group(2).replace('-', '_')
            filename = f"episode_{episode_num}_{episode_title}.txt"
        else:
            # Fallback filename
            filename = f"episode_{hash(episode_url)}.txt"
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Episode URL: {episode_url}\n")
                f.write("=" * 80 + "\n\n")
                f.write(transcript)
            
            print(f"Saved transcript to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saving transcript: {e}")
            return None
    
    def get_episodes_from_api(self, max_episodes=3):
        """Get episode URLs from WordPress API"""
        print(f"Fetching episode URLs from WordPress API (max {max_episodes})...")
        
        api_url = "https://www.iwillteachyoutoberich.com/wp-json/wp/v2/posts"
        
        try:
            # Try to get more posts to find episodes - try multiple requests if needed
            episode_urls = []
            page = 1
            
            while len(episode_urls) < max_episodes and page <= 5:  # Limit to 5 pages to avoid too many requests
                print(f"Fetching page {page}...")
                response = self.safe_request(api_url, params={'per_page': 50, 'page': page})
                if not response:
                    print(f"Failed to fetch API data for page {page}")
                    break
                
                data = response.json()
                print(f"Found {len(data)} posts in API response for page {page}")
                
                if not data:  # No more posts
                    break
                
                for post in data:
                    if len(episode_urls) >= max_episodes:
                        break
                        
                    title = post.get('title', {}).get('rendered', '').lower()
                    slug = post.get('slug', '').lower()
                    link = post.get('link', '')
                    content = post.get('content', {}).get('rendered', '')
                    
                    # Check if this looks like a podcast episode
                    if ('episode' in title or 'episode' in slug or 
                        re.search(r'\d+', slug) or 
                        'podcast' in title or 'podcast' in slug):
                        
                        if link not in episode_urls:
                            episode_urls.append(link)
                            print(f"Found episode {len(episode_urls)}: {link}")
                            
                            # Check if it has transcript content
                            if 'transcript' in content.lower():
                                print(f"  *** Has transcript content")
                
                page += 1
            
            print(f"Found {len(episode_urls)} episode URLs from API across {page-1} pages")
            return episode_urls
            
        except Exception as e:
            print(f"Error fetching episodes from API: {e}")
            return []
    
    def extract_episode_number(self, url):
        """Extract episode number from URL"""
        match = re.search(r'/(\d+)-', url)
        if match:
            return int(match.group(1))
        return None
    
    def save_combined_transcripts(self, transcripts_data, output_dir="transcripts"):
        """Save all transcripts to a single file with episode range in filename"""
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
            
            print(f"Saved combined transcripts to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saving combined transcripts: {e}")
            return None
    
    def scrape_all_transcripts(self):
        """Main method to scrape all podcast transcripts"""
        print("Starting podcast transcript scraper...")
        
        # Get episode links from WordPress API (more comprehensive)
        episode_links = self.get_episodes_from_api(max_episodes=3)
        
        if not episode_links:
            print("No episode links found from API. Trying main page...")
            # Fallback to main page scraping
            episode_links = self.get_episode_links(max_episodes=3)
        
        if not episode_links:
            print("No episode links found. Trying alternative approach...")
            # Try to manually add some known episode URLs
            episode_links = [
                "https://www.iwillteachyoutoberich.com/194-lakiesha-james-2/",
                # Add more episode URLs as needed
            ]
        
        print(f"\nFound {len(episode_links)} episode URLs:")
        print("=" * 80)
        for i, url in enumerate(episode_links, 1):
            print(f"{i:2d}. {url}")
        print("=" * 80)
        
        # Scrape transcripts for all episodes
        print(f"\nScraping transcripts for {len(episode_links)} episodes...")
        transcripts_data = []
        successful_scrapes = 0
        
        for i, episode_url in enumerate(episode_links, 1):
            print(f"\n[{i}/{len(episode_links)}] Processing: {episode_url}")
            
            transcript = self.extract_transcript(episode_url)
            if transcript:
                transcripts_data.append((episode_url, transcript))
                successful_scrapes += 1
                print(f"  ✓ Successfully extracted transcript ({len(transcript)} characters)")
            else:
                print(f"  ✗ Failed to extract transcript")
        
        # Save all transcripts to a single file
        if transcripts_data:
            print(f"\nSaving {len(transcripts_data)} transcripts to combined file...")
            filepath = self.save_combined_transcripts(transcripts_data)
            if filepath:
                print(f"✓ Successfully saved combined transcripts to: {filepath}")
            else:
                print("✗ Failed to save combined transcripts")
        else:
            print("No transcripts to save")
        
        print(f"\nScraping complete! Successfully scraped {successful_scrapes}/{len(episode_links)} transcripts.")

def main():
    scraper = PodcastScraper()
    scraper.scrape_all_transcripts()

if __name__ == "__main__":
    main() 