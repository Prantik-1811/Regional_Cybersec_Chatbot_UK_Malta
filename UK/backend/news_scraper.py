import feedparser
import time
import re
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio

class NewsScraper:
    def __init__(self, cache_duration_seconds: int = 600):
        # Cache to avert spamming the feeds on every page refresh (default 10 minutes)
        self.cache_duration = cache_duration_seconds
        self.last_fetch_time = 0
        self.cached_articles: List[Dict] = []
        
        # A list of authoritative cybersecurity RSS feeds
        self.rss_feeds = [
            "https://feeds.feedburner.com/TheHackersNews",
            "https://www.bleepingcomputer.com/feed/",
            "https://krebsonsecurity.com/feed/",
            "https://www.ncsc.gov.uk/api/1/services/v1/news-rss.xml"
        ]

    def _get_category(self, title: str, content: str) -> str:
        """
        Determine category based on keywords in title or content.
        Uses a similar heuristic to update_checker for consistency.
        """
        text_lower = (title + " " + content).lower()
        if 'physical' in text_lower: return 'Physical Security'
        if 'technical' in text_lower: return 'Technical Security'
        if 'iot' in text_lower or 'internet-of-things' in text_lower: return 'IoT Security'
        if 'threat' in text_lower: return 'Threat Intelligence'
        if 'career' in text_lower: return 'Careers'
        if 'malware' in text_lower or 'ransomware' in text_lower: return 'Malware'
        if 'social' in text_lower or 'scam' in text_lower or 'phishing' in text_lower: return 'Social Engineering'
        if 'hacker' in text_lower or 'nation-state' in text_lower: return 'Threat Actors'
        if 'attack' in text_lower or 'supply-chain' in text_lower: return 'Attack Vectors'
        if 'vulnerabilit' in text_lower or 'cve' in text_lower or 'flaw' in text_lower: return 'Vulnerabilities'
        if 'cryptograph' in text_lower or 'quantum' in text_lower: return 'Cryptography'
        if 'governance' in text_lower or 'protection' in text_lower: return 'Governance'
        return 'Cyber Security'

    def _clean_html(self, raw_html: str) -> str:
        """
        Strip HTML tags from the excerpt/content for display, returning plain text.
        """
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator=" ").strip()

    def _generate_excerpt(self, text: str, max_len: int = 200) -> str:
        """
        Generate a short excerpt from plain text.
        """
        if len(text) <= max_len:
            return text
        
        # Try to cut off cleanly near the max_len
        cut_text = text[:max_len]
        last_space = cut_text.rfind(" ")
        if last_space > 0:
            return cut_text[:last_space] + "..."
        return cut_text + "..."

    async def fetch_articles_async(self) -> List[Dict]:
        """
        Async wrapper if needed, though feedparser is synchronous. 
        We use asyncio.to_thread to prevent blocking the event loop.
        """
        return await asyncio.to_thread(self.fetch_articles)

    def fetch_articles(self) -> List[Dict]:
        """
        Fetch and parse articles from the RSS feeds.
        Utilizes caching so it doesn't do network I/O if recently fetched.
        """
        current_time = time.time()
        
        # Return cached articles if within the cache duration
        if current_time - self.last_fetch_time < self.cache_duration and self.cached_articles:
            return self.cached_articles

        articles = []
        for feed_url in self.rss_feeds:
            try:
                parsed = feedparser.parse(feed_url)
                for entry in parsed.entries[:5]: # Get up to 5 latest from each feed
                    title = entry.get('title', 'Unknown Title')
                    link = entry.get('link', '')
                    
                    # Try to get the fullest content possible from the RSS feed
                    content_html = ""
                    if 'content' in entry and len(entry.content) > 0:
                        content_html = entry.content[0].value
                    elif 'summary' in entry:
                        content_html = entry.summary
                    elif 'description' in entry:
                        content_html = entry.description
                        
                    plain_text = self._clean_html(content_html)
                    
                    # Ensure we have at least some content
                    if not plain_text:
                        plain_text = title

                    category = self._get_category(title, plain_text)
                    excerpt = self._generate_excerpt(plain_text)

                    articles.append({
                        'url': link,
                        'title': title,
                        'excerpt': excerpt,
                        'full_content': plain_text,
                        'category': category,
                        'type': 'rss'
                    })
            except Exception as e:
                print(f"Error fetching RSS feed '{feed_url}': {e}")
                
        # Update cache
        if articles:
            # Sort by a combination or just return them (most feeds are chronological)
            self.cached_articles = articles
            self.last_fetch_time = current_time

        return self.cached_articles
