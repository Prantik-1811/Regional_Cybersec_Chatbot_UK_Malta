import asyncio
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from playwright.async_api import async_playwright
from io import BytesIO
from pdfminer.high_level import extract_text

START_URL = "https://ncc-mita.gov.mt/"
MAX_PAGES = 200
REQUEST_DELAY = 1

# ----------- Helpers -----------
def normalize_url(url):
    url, _ = urldefrag(url)
    return url.rstrip("/")

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_visible_text(html):
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    texts = []
    for tag in soup.find_all(["p", "li", "h1", "h2", "h3", "h4"]):
        t = tag.get_text(" ", strip=True)
        if t:
            texts.append(t)

    return clean_text(" ".join(texts))

def extract_pdf_text(url):
    try:
        r = requests.get(url, timeout=15)
        return clean_text(extract_text(BytesIO(r.content)))
    except Exception:
        return ""

# ----------- Main Scraper -----------
async def run():
    visited = set()
    queue = [normalize_url(START_URL)]
    results = []

    domain = urlparse(START_URL).netloc

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        # 🚫 Block non-text resources
        async def block_resources(route):
            if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", block_resources)

        page = await context.new_page()

        while queue and len(visited) < MAX_PAGES:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                print(f"[+] Scraping: {url}")

                # ---------- PDF ----------
                if url.lower().endswith(".pdf"):
                    text = extract_pdf_text(url)
                    results.append({
                        "url": url,
                        "type": "pdf",
                        "content": text
                    })

                # ---------- HTML ----------
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                html = await page.content()
                text = extract_visible_text(html)

                results.append({
                    "url": url,
                    "type": "html",
                    "content": text
                })

                # discover links
                soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    link = normalize_url(urljoin(START_URL, a["href"]))
                    if urlparse(link).netloc == domain and link not in visited:
                        queue.append(link)

                await asyncio.sleep(REQUEST_DELAY)

            except Exception as e:
                print(f"[-] Error: {e}")

        await browser.close()

    return results

# ----------- Entry Point -----------
if __name__ == "__main__":
    data = asyncio.run(run())

    with open("cyber_chatbot_maltaNCC.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[✓] Collected {len(data)} valid text documents")
