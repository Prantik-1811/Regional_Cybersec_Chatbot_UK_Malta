"""
Reliable Selenium Stealth Scraper - Works with Chrome 144
Falls back to standard Selenium with maximum stealth configuration
More compatible than undetected-chromedriver
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from io import BytesIO
from pdfminer.high_level import extract_text
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import time
import random

START_URL = "https://www.reliancecyber.com/reliance-cyber-ncsc-assured-cyber-incident-response-provider/"
MAX_PAGES = 200
REQUEST_DELAY = 4
MIN_DELAY = 3
MAX_DELAY = 7

# ----------- Helpers -----------
def normalize_url(url):
    url, _ = urldefrag(url)
    return url.rstrip("/")

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_visible_text(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()
    texts = []
    for tag in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div", "span", "article", "section"]):
        t = tag.get_text(" ", strip=True)
        if t and len(t) > 20:
            texts.append(t)
    return clean_text(" ".join(texts))

def extract_pdf_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, timeout=15, headers=headers)
        return clean_text(extract_text(BytesIO(r.content)))
    except Exception as e:
        return ""

def is_blocked_page(html, url):
    """Detect block pages"""
    block_indicators = [
        'access denied', 'blocked', '403 forbidden', 'cloudflare',
        'checking your browser', 'attention required', 'security check',
        'ray id', 'error 1020', 'ddos protection'
    ]
    html_lower = html.lower()
    
    detected = [i for i in block_indicators if i in html_lower]
    
    if detected:
        print(f"[!] BLOCKED: {detected}")
        return True, detected
    
    if len(extract_visible_text(html)) < 100:
        return True, ["short_content"]
    
    return False, []

def has_actual_content(html, min_length=200):
    return len(extract_visible_text(html)) > min_length

# ----------- Selenium Stealth Scraper -----------
class SeleniumStealthScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Initialize Selenium with maximum stealth"""
        print("\n" + "="*60)
        print("INITIALIZING SELENIUM WITH STEALTH")
        print("="*60)
        
        try:
            options = webdriver.ChromeOptions()
            
            # Core stealth arguments
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Additional arguments
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--start-maximized')
            options.add_argument('--window-size=1920,1080')
            
            # Disable logging
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Preferences
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            options.add_experimental_option("prefs", prefs)
            
            print("[→] Starting Chrome...")
            self.driver = webdriver.Chrome(options=options)
            
            # Apply stealth.js
            print("[→] Applying stealth configuration...")
            stealth(
                self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            # Additional JavaScript patches
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
            })
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(10)
            
            print("[✓] Selenium with stealth ready!")
            print("[✓] This should work with Chrome 144")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n[✗] Failed to initialize Selenium!")
            print(f"[✗] Error: {e}")
            print("\n" + "="*60)
            print("TROUBLESHOOTING:")
            print("="*60)
            print("\n1. Make sure Chrome is installed")
            print("\n2. Install/Update packages:")
            print("   pip install --upgrade selenium selenium-stealth")
            print("\n3. Chrome should auto-download the right driver")
            print("\n4. If still failing, manually install ChromeDriver:")
            print("   - Download from: https://googlechromelabs.github.io/chrome-for-testing/")
            print("   - Match your Chrome version (144)")
            print("   - Place in PATH or specify location")
            print("="*60 + "\n")
            raise
    
    def random_delay(self, min_sec=None, max_sec=None):
        if min_sec is None:
            min_sec = MIN_DELAY
        if max_sec is None:
            max_sec = MAX_DELAY
        time.sleep(random.uniform(min_sec, max_sec))
    
    def human_scroll(self):
        try:
            for _ in range(random.randint(2, 4)):
                scroll = random.randint(300, 600)
                self.driver.execute_script(f"window.scrollBy(0, {scroll});")
                time.sleep(random.uniform(0.3, 0.8))
            
            scroll_up = random.randint(100, 300)
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_up});")
            time.sleep(random.uniform(0.2, 0.5))
        except:
            pass
    
    def wait_for_page_load(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except:
            return False
    
    def fetch_page(self, url, attempt=1, max_attempts=3):
        try:
            print(f"\n{'='*60}")
            print(f"[→] {url}")
            print(f"[→] Attempt {attempt}/{max_attempts}")
            print(f"{'='*60}")
            
            self.driver.get(url)
            self.random_delay(2, 4)
            
            self.wait_for_page_load(timeout=30)
            
            self.human_scroll()
            self.random_delay(1, 2)
            
            html = self.driver.page_source
            current_url = self.driver.current_url
            
            is_blocked, reasons = is_blocked_page(html, current_url)
            
            if is_blocked:
                print(f"[✗] BLOCKED: {reasons}")
                
                try:
                    self.driver.save_screenshot(f"blocked_{int(time.time())}.png")
                except:
                    pass
                
                if attempt < max_attempts:
                    wait = attempt * 10
                    print(f"[↻] Waiting {wait}s...")
                    time.sleep(wait)
                    return self.fetch_page(url, attempt + 1, max_attempts)
                return html, False
            
            if has_actual_content(html, 100):
                length = len(extract_visible_text(html))
                print(f"[✓] Success! {length} chars")
                return html, True
            else:
                if attempt < max_attempts:
                    self.random_delay(3, 5)
                    return self.fetch_page(url, attempt + 1, max_attempts)
                return html, False
            
        except Exception as e:
            print(f"[✗] Error: {e}")
            if attempt < max_attempts:
                time.sleep(5)
                return self.fetch_page(url, attempt + 1, max_attempts)
            return "", False
    
    def close(self):
        try:
            if self.driver:
                self.driver.quit()
                print("\n[✓] Browser closed")
        except:
            pass

# ----------- Main Scraper -----------
def run_scraper():
    visited = set()
    queue = [normalize_url(START_URL)]
    results = []
    failed_urls = []
    blocked_count = 0
    
    domain = urlparse(START_URL).netloc
    
    print("\n🚀 Starting Selenium Stealth Scraper...")
    print("📌 Compatible with Chrome 144")
    print("📌 More stable than undetected-chromedriver\n")
    
    try:
        scraper = SeleniumStealthScraper()
    except Exception as e:
        print(f"[✗] Cannot start: {e}")
        return []
    
    try:
        while queue and len(visited) < MAX_PAGES:
            url = queue.pop(0)
            
            if url in visited:
                continue
            
            visited.add(url)
            
            print(f"\n📊 Progress: {len(visited)}/{MAX_PAGES} | Queue: {len(queue)}")
            
            if url.lower().endswith(".pdf"):
                text = extract_pdf_text(url)
                results.append({"url": url, "type": "pdf", "content": text})
                continue
            
            html, success = scraper.fetch_page(url)
            
            if not success:
                is_blocked, _ = is_blocked_page(html, url)
                if is_blocked:
                    blocked_count += 1
                failed_urls.append(url)
                
                if blocked_count > 3:
                    print(f"\n[!] Multiple blocks ({blocked_count}), increasing delays...")
                    global MIN_DELAY, MAX_DELAY, REQUEST_DELAY
                    MIN_DELAY += 2
                    MAX_DELAY += 3
                    REQUEST_DELAY += 2
                
                continue
            
            text = extract_visible_text(html)
            results.append({"url": url, "type": "html", "content": text})
            
            soup = BeautifulSoup(html, "lxml")
            new_links = 0
            
            for a in soup.find_all("a", href=True):
                try:
                    link = normalize_url(urljoin(url, a["href"]))
                    if (urlparse(link).netloc == domain and 
                        link not in visited and 
                        link not in queue):
                        queue.append(link)
                        new_links += 1
                except:
                    continue
            
            print(f"[+] Found {new_links} new links")
            
            delay = random.uniform(REQUEST_DELAY, REQUEST_DELAY + 2)
            print(f"[⏳] Waiting {delay:.1f}s...")
            time.sleep(delay)
        
    except KeyboardInterrupt:
        print("\n[!] Stopped by user")
    except Exception as e:
        print(f"\n[✗] Error: {e}")
    finally:
        scraper.close()
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"✓ Scraped: {len(results)}")
    print(f"✗ Failed: {len(failed_urls)}")
    print(f"🚫 Blocked: {blocked_count}")
    print(f"{'='*60}\n")
    
    if failed_urls:
        print("Failed URLs (first 10):")
        for url in failed_urls[:10]:
            print(f"  - {url}")
    
    return results

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SELENIUM STEALTH SCRAPER")
    print("Chrome 144 Compatible - Stable Fallback Solution")
    print("="*60)
    print("\n💡 This uses standard Selenium + stealth")
    print("💡 More compatible than undetected-chromedriver")
    print("💡 Works with any Chrome version")
    print("="*60 + "\n")
    
    input("Press ENTER to start, or Ctrl+C to cancel...")
    
    data = run_scraper()
    
    if data:
        output_file = "cyber_chatbot_UK4.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        total = sum(len(item.get('content', '')) for item in data)
        
        print(f"\n✅ SUCCESS!")
        print(f"📄 Saved: {output_file}")
        print(f"📊 Documents: {len(data)}")
        print(f"📝 Total chars: {total:,}")
    else:
        print("\n[!] No data collected - check errors above")