import json
import os
import glob
import re

# ==========================================
# Script Purpose:
# This is an enhanced version of the PDF inspection script.
# It targets specific JSON files for a deeper dive, particularly for UK data.
# It also attempts to find context where 'pdf' is mentioned in the text content.
# ==========================================

scraped_dir = r"d:\Prantik\Chatbot_Deepcytes\Scraped files"

# List of specific filenames to check. 
# This allows focusing the debugging/inspection on recognized problem areas or key datasets.
files_to_check = [
    "cyber_chatbot_UK1.json", 
    "cyber_chatbot_UK2.json", 
    "cyber_chatbot_UK3.json", 
    "cyber_chatbot_UK4.json", 
    "cyber_chatbot_UK_artic.json"
]

print(f"Checking {len(files_to_check)} specific files.")

# Iterate through the specific list of files.
for filename in files_to_check:
    # Construct the full path to the file.
    json_file = os.path.join(scraped_dir, filename)
    
    # Check if the file actually exists before trying to read it.
    if not os.path.exists(json_file):
        print(f"File not found: {filename}")
        continue
        
    print(f"Inspecting {filename}...")
    try:
        # Load the JSON data.
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        pdf_urls = []
        
        # Iterate through items to find PDFs and pattern matches.
        for item in data:
            url = item.get('url', '')
            type_ = item.get('type', '')
            content = item.get('content', '')
            
            # 1. Direct Identification: Check 'type' field or URL extension.
            if type_ and type_.lower() == 'pdf':
                pdf_urls.append(url)
            elif url and url.lower().endswith('.pdf'):
                pdf_urls.append(url)
            
            # 2. Contextual Deep Dive (Targeted):
            # For 'cyber_chatbot_UK1.json', we look deeper into the text content.
            if filename == "cyber_chatbot_UK1.json" and 'pdf' in content.lower():
                # Find all occurrences of the substring 'pdf' (case-insensitive).
                # re.finditer returns an iterator of match objects.
                matches = [m.start() for m in re.finditer('pdf', content, re.IGNORECASE)]
                
                if matches:
                    print(f"  Found 'pdf' in content of {url[:50]}...")
                    # Loop through the first 3 matches to show snippets.
                    for pos in matches[:3]: 
                        # Extract a snippet of text around the match (50 chars before and after).
                        start = max(0, pos - 50)
                        end = min(len(content), pos + 50)
                        # Clean up newlines for cleaner console output.
                        snippet = content[start:end].replace('\n', ' ')
                        print(f"    Context: ...{snippet}...")

        # Summary for the file.
        print(f"  Extracted {len(set(pdf_urls))} unique PDF URLs from structure.")
            
    except Exception as e:
        print(f"  Error reading {filename}: {e}")
