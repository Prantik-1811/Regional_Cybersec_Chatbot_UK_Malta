import json

# Read the raw JSON and inspect first few entries
json_path = "Scraped files/cyber_chatbot_UK1.json"
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entries: {len(data)}")
print(f"Data type: {type(data)}")

if isinstance(data, list) and len(data) > 0:
    for i, item in enumerate(data[:3]):
        print(f"\n=== ENTRY {i} ===")
        print(f"  Type: {type(item)}")
        if isinstance(item, dict):
            print(f"  Keys: {list(item.keys())}")
            for k, v in item.items():
                val = str(v)[:100] if v else 'EMPTY/None'
                print(f"  {k}: {val}")
        elif isinstance(item, str):
            print(f"  String value: {item[:200]}")
