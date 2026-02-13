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
    
    def _extract_title(self, content: str, url: str) -> str:
        """Extract title from content (HTML or plain text) or URL."""
        # Try HTML parsing first
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
        
        # Plain text: use first meaningful line or sentence
        if content:
            # Split by newlines, take first non-empty line that's title-like
            for line in content.split('\n'):
                line = line.strip()
                # Good title: 10-120 chars, doesn't start with common non-title patterns
                if 10 < len(line) < 120 and not line.startswith(('Home /', 'http', 'www.', '©')):
                    return line
            # Fallback: first sentence
            first_sentence = content.split('.')[0].strip()
            if 10 < len(first_sentence) < 150:
                return first_sentence
        
        # URL-based fallback
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if path:
            # Take last meaningful path segment
            segment = path.split('/')[-1]
            title = segment.replace('-', ' ').replace('_', ' ')
            return title.title()[:100]
        
        # Last resort: use domain
        domain = parsed.netloc.replace('www.', '')
        return domain or "Unknown"
    
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
    
    def _get_category(self, url: str) -> str:
        """Derive category from URL path."""
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
        """Remove repeated breadcrumb-like prefixes from scraped content."""
        if not content:
            return ''
        # Many scraped pages have the content repeated multiple times
        # Take only first occurrence (up to ~40% of total) to avoid duplication
        half = len(content) // 3
        if half > 500:
            content = content[:half]
        # Strip leading "Home / ..." breadcrumb
        import re
        content = re.sub(r'^(Home\s*/\s*.*?(?:\n|(?=[A-Z][a-z])))', '', content, count=1).strip()
        return content

    def _generate_excerpt(self, content: str, max_len: int = 200) -> str:
        """Generate a clean excerpt from content."""
        clean = self._clean_content(content)
        # Find first sentence that's meaningful (>30 chars)
        sentences = clean.split('.')
        excerpt_parts = []
        total = 0
        for s in sentences:
            s = s.strip()
            if len(s) > 20 and total + len(s) < max_len:
                excerpt_parts.append(s)
                total += len(s)
        return '. '.join(excerpt_parts) + '...' if excerpt_parts else clean[:max_len] + '...'

    def get_articles(self, limit: int = 50) -> List[dict]:
        """Get articles from loaded sources for display."""
        articles = []
        seen_titles = set()
        for source in self.sources[:limit]:
            content = source.get('content', '')
            url = source.get('url', '')
            if not content or not url:
                continue
            title = self._extract_title(content, url)
            # Skip duplicates by title
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
