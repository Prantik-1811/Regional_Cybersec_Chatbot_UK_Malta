"""
Update Checker - Monitors source URLs for content changes.
Uses content hashing to detect when pages have been updated.
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
        self.json_path = Path(json_path)
        self.cache_path = Path(cache_path)
        self.sources: List[Dict] = []
        self.cache: Dict[str, dict] = {}
        self.total_sources = 0
        
        self._load_sources()
        self._load_cache()
    
    def _load_sources(self):
        """Load source URLs from JSON data file."""
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
        """Load hash cache from file."""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save hash cache to file."""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _hash_content(self, content: str) -> str:
        """Generate MD5 hash of content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _extract_title(self, html_content: str, url: str) -> str:
        """Extract title from HTML content or URL."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.text.strip()[:100]
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.text.strip()[:100]
        except:
            pass
        return url.split('/')[-1] or "Unknown"
    
    def is_ready(self) -> bool:
        """Check if update checker is ready."""
        return len(self.sources) > 0
    
    async def fetch_url(self, url: str, timeout: float = 10.0) -> Optional[str]:
        """Fetch content from URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=timeout, follow_redirects=True)
                if response.status_code == 200:
                    return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None
    
    async def check_single_url(self, source: dict) -> Optional[dict]:
        """Check a single URL for updates."""
        url = source.get('url', '')
        if not url:
            return None
        
        # Fetch current content
        current_content = await self.fetch_url(url)
        if not current_content:
            return None
        
        current_hash = self._hash_content(current_content)
        cached = self.cache.get(url, {})
        stored_hash = cached.get('hash')
        
        # Determine if content changed
        has_new_content = stored_hash is not None and current_hash != stored_hash
        
        # Update cache
        self.cache[url] = {
            'hash': current_hash,
            'last_checked': datetime.now().isoformat(),
            'title': self._extract_title(current_content, url)
        }
        
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
        Check multiple URLs for updates.
        Only checks a subset to avoid overwhelming servers.
        """
        updates = []
        sources_to_check = self.sources[:limit]
        
        tasks = [self.check_single_url(source) for source in sources_to_check]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                updates.append(result)
        
        self._save_cache()
        return updates
    
    def get_articles(self, limit: int = 10) -> List[dict]:
        """Get articles from loaded sources for display."""
        articles = []
        for source in self.sources[:limit]:
            content = source.get('content', '')[:300]
            articles.append({
                'url': source.get('url', ''),
                'title': self._extract_title(content, source.get('url', '')),
                'excerpt': content,
                'type': source.get('type', 'html')
            })
        return articles
