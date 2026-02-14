import json
import os
import glob
import requests
import re
from urllib.parse import urlparse

# ==========================================
# Configuration and Setup
# ==========================================
# Define the directories for input (scraped data) and output (training data).
# 'scraped_dir' contains the JSON files produced by the scraping process.
# 'output_dir' is where the processed PDFs and HTML files will be saved.
scraped_dir = r"d:\Prantik\Chatbot_Deepcytes\Scraped files"
output_dir = r"d:\Prantik\Chatbot_Deepcytes\Training_Data"

# Define specific subdirectories for organized storage of downloaded content.
pdf_dir = os.path.join(output_dir, "PDFs")
html_dir = os.path.join(output_dir, "HTMLs")

# Ensure that the output directories exist. If they don't, create them.
# exist_ok=True prevents errors if the directory already exists.
os.makedirs(pdf_dir, exist_ok=True)
os.makedirs(html_dir, exist_ok=True)

def sanitize_filename(url, extension):
    """
    Generates a safe and valid filename from a given URL.
    
    Args:
        url (str): The URL of the resource.
        extension (str): The desired file extension (e.g., '.pdf', '.html').
        
    Returns:
        str: A sanitized filename safe for the filesystem.
    """
    # Parse the URL to extract the path component.
    parsed = urlparse(url)
    path = parsed.path
    
    # Remove trailing slash if present to get the actual filename component.
    if path.endswith('/'):
        path = path[:-1]
    
    # Extract the basename (the last part of the path).
    filename = os.path.basename(path)
    
    # If the URL path is empty or doesn't yield a filename (e.g., root domain),
    # fallback to using the network location (domain name).
    if not filename:
        filename = parsed.netloc
        
    # Remove characters that are invalid in Windows filenames (<, >, :, ", /, \, |, ?, *).
    # replace them with an underscore.
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Ensure the filename ends with the correct extension.
    # If not, append the extension to the filename.
    if not filename.lower().endswith(extension):
        filename += extension
        
    return filename

def download_pdf(url, save_path):
    """
    Downloads a PDF file from a specified URL and saves it to the local path.
    
    Args:
        url (str): The direct URL of the PDF.
        save_path (str): The full local path where the PDF should be saved.
        
    Returns:
        bool: True if download was successful, False otherwise.
    """
    try:
        # Send a GET request to the URL.
        # stream=True is used to handle large files efficiently by not loading the whole content into memory at once.
        # timeout=15 ensures the script doesn't hang indefinitely if the server is unresponsive.
        response = requests.get(url, stream=True, timeout=15)
        
        # Check if the request was successful (status code 200). 
        # Raises an HTTPError if the status is 4xx or 5xx.
        response.raise_for_status()
        
        # Open the local file in binary write mode ('wb').
        with open(save_path, 'wb') as f:
            # Iterate over the response content in chunks of 8KB.
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"  [PDF] Downloaded: {url} -> {os.path.basename(save_path)}")
        return True
    except Exception as e:
        # specific error handling or logging could be added here.
        print(f"  [PDF] Failed to download {url}: {e}")
        return False

def save_html_content(url, content, save_path):
    """
    Saves raw text or HTML fragments into a structured HTML file.
    
    Args:
        url (str): The source URL of the content (added as metadata).
        content (str): The raw HTML or text content to save.
        save_path (str): The full local path where the HTML file should be saved.
        
    Returns:
        bool: True if saving was successful, False otherwise.
    """
    try:
        # Wrap the raw content in a basic HTML5 boilerplate structure.
        # This ensures the saved file is a valid HTML document and preserves metadata like the source URL.
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
        # Write the constructed HTML content to the file using UTF-8 encoding.
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"  [HTML] Saved: {url} -> {os.path.basename(save_path)}")
        return True
    except Exception as e:
        print(f"  [HTML] Failed to save {url}: {e}")
        return False

def process_files():
    """
    Main execution function.
    Iterates through all JSON files in the scraped directory and processes their content.
    Identifies and downloads PDFs, and saves other content as HTML files.
    """
    # Find all .json files in the scraped directory.
    json_files = glob.glob(os.path.join(scraped_dir, "*.json"))
    print(f"Found {len(json_files)} JSON files to process.")
    
    # Initialize counters for reporting statistics at the end.
    pdf_count = 0
    html_count = 0
    
    # Check sets to avoid processing the same URL multiple times (deduplication).
    processed_pdf_urls = set()
    processed_html_urls = set()

    # Iterate through each found JSON file.
    for json_file in json_files:
        print(f"\nProcessing {os.path.basename(json_file)}...")
        try:
            # Open and load the JSON data.
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Iterate through each item (scraped page/resource) in the JSON data.
            for item in data:
                url = item.get('url', '')
                type_ = item.get('type', '').lower()
                content = item.get('content', '')
                
                # Skip items without a URL as we can't process them or deduplicate them.
                if not url:
                    continue

                # -------------------------
                # PDF Processing Logic
                # -------------------------
                # Check if the item is explicitly marked as 'pdf' or if the URL ends with .pdf.
                if type_ == 'pdf' or url.lower().endswith('.pdf'):
                    # Skip if we've already processed this PDF URL.
                    if url in processed_pdf_urls:
                        continue
                    
                    # Generate a local filename and full path.
                    filename = sanitize_filename(url, '.pdf')
                    save_path = os.path.join(pdf_dir, filename)
                    
                    # Attempt to download the PDF.
                    if download_pdf(url, save_path):
                        pdf_count += 1
                        processed_pdf_urls.add(url) # Mark as processed

                # -------------------------
                # HTML Processing Logic
                # -------------------------
                # If it's not a PDF, we treat it as HTML content.
                # We check if there is actual 'content' to save.
                elif content:
                     # Skip if we've already processed this URL.
                     if url in processed_html_urls:
                        continue
                     
                     # Generate a local filename and full path.
                     filename = sanitize_filename(url, '.html')
                     save_path = os.path.join(html_dir, filename)
                     
                     # Save the content as an HTML file.
                     if save_html_content(url, content, save_path):
                         html_count += 1
                         processed_html_urls.add(url) # Mark as processed
                         
        except Exception as e:
            # Catching generic exceptions to ensure one bad file doesn't crash the whole process.
            print(f"Error processing {json_file}: {e}")

    # Final summary of the operation.
    print(f"\nProcessing complete.")
    print(f"Total PDFs downloaded: {pdf_count}")
    print(f"Total HTMLs saved: {html_count}")
    print(f"Data saved to: {output_dir}")

if __name__ == "__main__":
    # Execute the main processing function when script is run directly.
    process_files()
