"""
Update Checker Module

This module monitors external cybersecurity sources for new content.
It serves two main purposes:
1. Detecting when a scraped URL source has actually changed (using content hashing).
2. Serving the "Latest News" feed by cleaning and formatting the scraped content.

Key Features:
- MD5 Hashing to minimize redundant alerts.
- Asynchronous fetching for speed.
- Heuristic extraction of Titles and Categories from raw HTML/Text.
"""

import json
import hashlib
import httpx
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import asyncio
from bs4 import BeautifulSoup


class UpdateChecker:
    def __init__(self, json_path: str, cache_path: str = "./update_cache.json"):
        """
        Initialize the update checker.
        
        Args:
            json_path (str): Path to the source JSON file containing URLs.
            cache_path (str): Path to store the 'last seen' state of URLs.
        """
        self.json_path = Path(json_path)
        self.cache_path = Path(cache_path)
        self.sources: List[Dict] = []
        self.cache: Dict[str, dict] = {}
        self.total_sources = 0
        
        self._load_sources()
        self._load_cache()
    
    def _load_sources(self):
        """Load the list of sources to monitor from the scraped data file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sources = data if isinstance(data, list) else []
                self.total_sources = len(self.sources)
                print(f"Loaded {self.total_sources} sources from {self.json_path}")
        except Exception as e:
            print(f"Error loading sources: {e}")
            self.sources = []
    
    def _load_cache(self):
        """Load the persistent cache of previous checks."""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Persist the current state of checks to disk."""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _hash_content(self, content: str) -> str:
        """Create a fingerprint of the content to detect changes."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _extract_title(self, content: str, url: str) -> str:
        """
        Attempt to derive a meaningful title for a piece of content.
        Tries: HTML tags -> First logical sentence -> URL slug -> Domain name.
        """
        # Strategy 1: HTML parsing (if content looks like HTML)
        try:
            soup = BeautifulSoup(content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and title_tag.text.strip():
                return title_tag.text.strip()[:100]
            h1_tag = soup.find('h1')
            if h1_tag and h1_tag.text.strip():
                return h1_tag.text.strip()[:100]
        except:
            pass
        
        # Strategy 2: Plain text analysis
        if content:
            # Look for a short, non-URL first line
            for line in content.split('\n'):
                line = line.strip()
                if 10 < len(line) < 120 and not line.startswith(('Home /', 'http', 'www.', '©')):
                    return line
            # Fallback to first sentence
            first_sentence = content.split('.')[0].strip()
            if 10 < len(first_sentence) < 150:
                return first_sentence
        
        # Strategy 3: URL Path analysis
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if path:
            segment = path.split('/')[-1]
            title = segment.replace('-', ' ').replace('_', ' ')
            return title.title()[:100]
        
        # Strategy 4: Domain Name
        domain = parsed.netloc.replace('www.', '')
        return domain or "Unknown"
    
    def is_ready(self) -> bool:
        """Helper to check if sources are loaded."""
        return len(self.sources) > 0
    
    async def fetch_url(self, url: str, timeout: float = 10.0) -> Optional[str]:
        """Async fetch of a URL with error handling."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=timeout, follow_redirects=True)
                if response.status_code == 200:
                    return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None
    
    async def check_single_url(self, source: dict) -> Optional[dict]:
        """
        Verify a single source against its cached state.
        Returns an update object ONLY if content has changed.
        """
        url = source.get('url', '')
        if not url:
            return None
        
        # 1. Fetch live content
        current_content = await self.fetch_url(url)
        if not current_content:
            return None
        
        # 2. Compare Hash
        current_hash = self._hash_content(current_content)
        cached = self.cache.get(url, {})
        stored_hash = cached.get('hash')
        
        has_new_content = stored_hash is not None and current_hash != stored_hash
        
        # 3. Update State
        self.cache[url] = {
            'hash': current_hash,
            'last_checked': datetime.now().isoformat(),
            'title': self._extract_title(current_content, url)
        }
        
        # 4. Report if interesting
        if has_new_content or stored_hash is None:
            return {
                'url': url,
                'title': self.cache[url]['title'],
                'has_new_content': has_new_content,
                'last_checked': self.cache[url]['last_checked']
            }
        return None
    
    async def check_for_updates(self, limit: int = 10) -> List[dict]:
        """
        Main entry point for update checking.
        Checks a subset (limit) of sources concurrently.
        """
        updates = []
        # Slice to avoid checking thousands of URLs at once
        sources_to_check = self.sources[:limit]
        
        # Run checks in parallel
        tasks = [self.check_single_url(source) for source in sources_to_check]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                updates.append(result)
        
        self._save_cache()
        return updates
    
    # ==================================================
    # ARTICLE PROCESSING HELPERS (Category, Clean, Excerpt)
    # ==================================================

    def _get_category(self, url: str) -> str:
        """
        Determine category based on keywords in the URL.
        Useful for tagging articles without explicit metadata.
        """
        url_lower = url.lower()
        if 'physical' in url_lower: return 'Physical Security'
        if 'technical' in url_lower: return 'Technical Security'
        if 'human' in url_lower: return 'Human Security'
        if 'iot' in url_lower or 'internet-of-things' in url_lower: return 'IoT Security'
        if 'threat' in url_lower: return 'Threat Intelligence'
        if 'career' in url_lower: return 'Careers'
        if 'malware' in url_lower or 'ransomware' in url_lower: return 'Malware'
        if 'social-engineering' in url_lower or 'scam' in url_lower: return 'Social Engineering'
        if 'hacker' in url_lower or 'nation-state' in url_lower: return 'Threat Actors'
        if 'attack' in url_lower or 'supply-chain' in url_lower: return 'Attack Vectors'
        if 'vulnerabilit' in url_lower: return 'Vulnerabilities'
        if 'cryptograph' in url_lower or 'quantum' in url_lower: return 'Cryptography'
        if 'governance' in url_lower or 'protection' in url_lower: return 'Governance'
        return 'Cyber Security'

    def _clean_content(self, content: str) -> str:
        """
        Remove scraping artifacts like redundant breadcrumbs or menus.
        """
        if not content:
            return ''
        
        # Optimization: Scraped content often duplicates itself. 
        # We take the first 1/3rd as a heuristic for the "main" content if it's huge.
        half = len(content) // 3
        if half > 500:
            content = content[:half]
            
        # Regex to strip common "Home / Category / Title" breadcrumb strings
        import re
        content = re.sub(r'^(Home\s*/\s*.*?(?:\n|(?=[A-Z][a-z])))', '', content, count=1).strip()
        return content

    def _generate_excerpt(self, content: str, max_len: int = 200) -> str:
        """Generate a short preview text for cards."""
        clean = self._clean_content(content)
        
        # Try to find a complete sentence that has enough meat (>20 chars)
        sentences = clean.split('.')
        excerpt_parts = []
        total = 0
        for s in sentences:
            s = s.strip()
            if len(s) > 20 and total + len(s) < max_len:
                excerpt_parts.append(s)
                total += len(s)
        
        # Return properly ellipsized string
        result = '. '.join(excerpt_parts)
        if not result:
            return clean[:max_len] + '...'
        return result + '...'

    def get_articles(self, limit: int = 50) -> List[dict]:
        """
        Transform raw source data into frontend-ready Article objects.
        Filters out duplicates and minimal content.
        """
        articles = []
        seen_titles = set()
        
        for source in self.sources[:limit]:
            content = source.get('content', '')
            url = source.get('url', '')
            
            if not content or not url:
                continue
                
            title = self._extract_title(content, url)
            
            # Deduplication
            if title in seen_titles:
                continue
            seen_titles.add(title)
            
            articles.append({
                'url': url,
                'title': title,
                'excerpt': self._generate_excerpt(content),
                'full_content': self._clean_content(content),
                'category': self._get_category(url),
                'type': source.get('type', 'html')
            })
            
        return articles
