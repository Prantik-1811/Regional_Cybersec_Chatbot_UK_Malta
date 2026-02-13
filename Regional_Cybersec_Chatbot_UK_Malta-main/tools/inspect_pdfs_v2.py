import json
import os
import glob
import re

scraped_dir = r"d:\Prantik\Chatbot_Deepcytes\Scraped files"
# Focus on UK1 for deep dive, and others for general count
files_to_check = ["cyber_chatbot_UK1.json", "cyber_chatbot_UK2.json", "cyber_chatbot_UK3.json", "cyber_chatbot_UK4.json", "cyber_chatbot_UK_artic.json"]

print(f"Checking {len(files_to_check)} specific files.")

for filename in files_to_check:
    json_file = os.path.join(scraped_dir, filename)
    if not os.path.exists(json_file):
        print(f"File not found: {filename}")
        continue
        
    print(f"Inspecting {filename}...")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        pdf_urls = []
        
        # Check for direct PDF types or URL extensions
        for item in data:
            url = item.get('url', '')
            type_ = item.get('type', '')
            content = item.get('content', '')
            
            if type_ and type_.lower() == 'pdf':
                pdf_urls.append(url)
            elif url and url.lower().endswith('.pdf'):
                pdf_urls.append(url)
            
            # Deep dive for UK1 context
            if filename == "cyber_chatbot_UK1.json" and 'pdf' in content.lower():
                matches = [m.start() for m in re.finditer('pdf', content, re.IGNORECASE)]
                if matches:
                    print(f"  Found 'pdf' in content of {url[:50]}...")
                    for pos in matches[:3]: # Show first 3 matches
                        start = max(0, pos - 50)
                        end = min(len(content), pos + 50)
                        snippet = content[start:end].replace('\n', ' ')
                        print(f"    Context: ...{snippet}...")

        print(f"  Extracted {len(set(pdf_urls))} unique PDF URLs from structure.")
            
    except Exception as e:
        print(f"  Error reading {filename}: {e}")
