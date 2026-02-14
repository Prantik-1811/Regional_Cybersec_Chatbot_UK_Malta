import json

# ==========================================
# Script Purpose:
# This script reads a raw JSON file and inspects its structure.
# It is useful for understanding the schema of the scraped data before processing.
# ==========================================

# Path to the specific JSON file we want to inspect.
json_path = "Scraped files/cyber_chatbot_UK1.json"

print(f"Reading file: {json_path}")

# Open the file and load the JSON content.
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Print high-level statistics.
print(f"Total entries: {len(data)}")
print(f"Data type: {type(data)}")

# If the data is a list (expected for scraped items), inspect the first few items.
if isinstance(data, list) and len(data) > 0:
    # Loop through the first 3 items (indices 0, 1, 2).
    for i, item in enumerate(data[:3]):
        print(f"\n=== ENTRY {i} ===")
        print(f"  Type: {type(item)}")
        
        # If the item is a dictionary, print its keys and values.
        if isinstance(item, dict):
            print(f"  Keys: {list(item.keys())}")
            for k, v in item.items():
                # Truncate values to 100 characters to avoid flooding the console with long text.
                val = str(v)[:100] if v else 'EMPTY/None'
                print(f"  {k}: {val}")
                
        # If the item is just a string, print it directly (truncated).
        elif isinstance(item, str):
            print(f"  String value: {item[:200]}")
