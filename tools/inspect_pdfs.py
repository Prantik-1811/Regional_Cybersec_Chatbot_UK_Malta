import json
import os
import glob

# ==========================================
# Script Purpose:
# This script inspects the scraped JSON files to count and identify PDF files.
# It helps in verifying how many PDFs were detected during the scraping process.
# ==========================================

# Directory containing the scraped JSON files.
scraped_dir = r"d:\Prantik\Chatbot_Deepcytes\Scraped files"

# Use glob to find all .json files in the specified directory.
json_files = glob.glob(os.path.join(scraped_dir, "*.json"))

print(f"Found {len(json_files)} JSON files.")

# Loop through each found JSON file to analyze its content.
for json_file in json_files:
    print(f"Inspecting {os.path.basename(json_file)}...")
    try:
        # Open and read the JSON file.
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Initialize lists and counters for PDFs found in this file.
        pdf_urls = []
        pdf_types = 0
        
        # Iterate through each scraped item in the JSON data.
        for item in data:
            url = item.get('url', '')
            type_ = item.get('type', '')
            content = item.get('content', '')
            
            # Check if the item is explicitly marked as a PDF type.
            if type_.lower() == 'pdf':
                pdf_types += 1
                pdf_urls.append(url)
            # Alternatively, check if the URL extension implies a PDF.
            elif url.lower().endswith('.pdf'):
                pdf_urls.append(url)
            
            # Optional: Heuristic check for PDF references within text content.
            # This logic detects if the text mentions '.pdf', which might indicate a missed link.
            if '.pdf' in content.lower():
                # Currently just a pass, but could be expanded to extract links using regex.
                pass

        # Output the findings for the current file.
        print(f"  Found {pdf_types} items with type='pdf'")
        print(f"  Found {len(pdf_urls)} URLs ending in .pdf")
        
        # If any PDFs were found, print a sample of the first 3 URLs for verification.
        if pdf_urls:
            print(f"  Sample URLs: {pdf_urls[:3]}")
            
    except Exception as e:
        print(f"  Error reading {json_file}: {e}")
