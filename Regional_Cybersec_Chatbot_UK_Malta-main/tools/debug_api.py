import requests
import json

try:
    response = requests.get('http://localhost:8001/api/articles?limit=10')
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response type: {type(data)}")
    
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        articles = data.get('articles', [])
        print(f"Articles count: {len(articles)}")
        if articles:
            for i, a in enumerate(articles[:5]):
                print(f"\n[{i}] Title: {a.get('title','?')}")
                print(f"    Category: {a.get('category','?')}")
                print(f"    URL: {a.get('url','?')[:80]}")
                print(f"    Excerpt: {a.get('excerpt','?')[:100]}")
                print(f"    Content len: {len(a.get('full_content',''))}")
        else:
            print("NO ARTICLES RETURNED!")
            # Check health
            health = requests.get('http://localhost:8001/api/health').json()
            print(f"Health: {health}")
    else:
        print(f"Unexpected response: {str(data)[:500]}")
except Exception as e:
    print(f"Exception: {e}")
