import json
import os
import glob
import requests
import re
from urllib.parse import urlparse

# Configuration
scraped_dir = r"d:\Prantik\Chatbot_Deepcytes\Scraped files"
output_dir = r"d:\Prantik\Chatbot_Deepcytes\Training_Data"
pdf_dir = os.path.join(output_dir, "PDFs")
html_dir = os.path.join(output_dir, "HTMLs")

# Ensure output directories exist
os.makedirs(pdf_dir, exist_ok=True)
os.makedirs(html_dir, exist_ok=True)

def sanitize_filename(url, extension):
    """Generates a safe filename from a URL."""
    parsed = urlparse(url)
    path = parsed.path
    if path.endswith('/'):
        path = path[:-1]
    
    filename = os.path.basename(path)
    if not filename:
        filename = parsed.netloc
        
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Ensure extension
    if not filename.lower().endswith(extension):
        filename += extension
        
    return filename

def download_pdf(url, save_path):
    """Downloads a PDF from a URL."""
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  [PDF] Downloaded: {url} -> {os.path.basename(save_path)}")
        return True
    except Exception as e:
        print(f"  [PDF] Failed to download {url}: {e}")
        return False

def save_html_content(url, content, save_path):
    """Saves HTML content to a file."""
    try:
        # Wrap content in basic HTML structure if it's just raw text text/fragments
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Scraped Content from {url}</title>
<source_url>{url}</source_url>
</head>
<body>
{content}
</body>
</html>
"""
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"  [HTML] Saved: {url} -> {os.path.basename(save_path)}")
        return True
    except Exception as e:
        print(f"  [HTML] Failed to save {url}: {e}")
        return False

def process_files():
    json_files = glob.glob(os.path.join(scraped_dir, "*.json"))
    print(f"Found {len(json_files)} JSON files to process.")
    
    pdf_count = 0
    html_count = 0
    
    processed_pdf_urls = set()
    processed_html_urls = set()

    for json_file in json_files:
        print(f"\nProcessing {os.path.basename(json_file)}...")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for item in data:
                url = item.get('url', '')
                type_ = item.get('type', '').lower()
                content = item.get('content', '')
                
                if not url:
                    continue

                # Handle PDFs
                if type_ == 'pdf' or url.lower().endswith('.pdf'):
                    if url in processed_pdf_urls:
                        continue
                    
                    filename = sanitize_filename(url, '.pdf')
                    save_path = os.path.join(pdf_dir, filename)
                    
                    if download_pdf(url, save_path):
                        pdf_count += 1
                        processed_pdf_urls.add(url)

                # Handle HTMLs
                # Assuming 'html' type or default content extraction
                # We save content for anything that isn't a PDF if it has content
                elif content:
                     if url in processed_html_urls:
                        continue
                     
                     filename = sanitize_filename(url, '.html')
                     save_path = os.path.join(html_dir, filename)
                     
                     if save_html_content(url, content, save_path):
                         html_count += 1
                         processed_html_urls.add(url)
                         
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

    print(f"\nProcessing complete.")
    print(f"Total PDFs downloaded: {pdf_count}")
    print(f"Total HTMLs saved: {html_count}")
    print(f"Data saved to: {output_dir}")

if __name__ == "__main__":
    process_files()
