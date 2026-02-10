import json
import os
import glob

scraped_dir = r"d:\Prantik\Chatbot_Deepcytes\Scraped files"
json_files = glob.glob(os.path.join(scraped_dir, "*.json"))

print(f"Found {len(json_files)} JSON files.")

for json_file in json_files:
    print(f"Inspecting {os.path.basename(json_file)}...")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        pdf_urls = []
        pdf_types = 0
        
        for item in data:
            url = item.get('url', '')
            type_ = item.get('type', '')
            content = item.get('content', '')
            
            if type_.lower() == 'pdf':
                pdf_types += 1
                pdf_urls.append(url)
            elif url.lower().endswith('.pdf'):
                pdf_urls.append(url)
            
            # Also check if content has links to PDFs (simple check)
            if '.pdf' in content.lower():
                # This is just a hint, extracting links from text is harder without regex
                pass

        print(f"  Found {pdf_types} items with type='pdf'")
        print(f"  Found {len(pdf_urls)} URLs ending in .pdf")
        if pdf_urls:
            print(f"  Sample URLs: {pdf_urls[:3]}")
            
    except Exception as e:
        print(f"  Error reading {json_file}: {e}")
