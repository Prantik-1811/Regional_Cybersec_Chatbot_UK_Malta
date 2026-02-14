import requests
import json

# ==========================================
# Script Purpose:
# This script tests the local API server to ensure it's running and returning data correctly.
# It specifically checks the '/api/articles' endpoint and optionally the health check.
# ==========================================

try:
    # Make a GET request to the local articles endpoint with a limit of 10.
    # This assumes the backend server is running on localhost port 8001.
    print("Sending request to http://localhost:8001/api/articles?limit=10...")
    response = requests.get('http://localhost:8001/api/articles?limit=10')
    
    print(f"Status Code: {response.status_code}")
    
    # Parse the JSON response from the server.
    data = response.json()
    print(f"Response type: {type(data)}")
    
    # Check if the returned data is a dictionary (expected format).
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        
        # Extract the list of articles.
        articles = data.get('articles', [])
        print(f"Articles count: {len(articles)}")
        
        # If articles are returned, print details of the first 5 for verification.
        if articles:
            for i, a in enumerate(articles[:5]):
                print(f"\n[{i}] Title: {a.get('title','?')}")
                print(f"    Category: {a.get('category','?')}")
                # Print truncated URL and Excerpt to keep output clean.
                print(f"    URL: {a.get('url','?')[:80]}")
                print(f"    Excerpt: {a.get('excerpt','?')[:100]}")
                # Check snippet length or full content length.
                print(f"    Content len: {len(a.get('full_content',''))}")
        else:
            # If no articles, check if the server is healthy.
            print("NO ARTICLES RETURNED!")
            
            # Call the health check endpoint.
            health = requests.get('http://localhost:8001/api/health').json()
            print(f"Health: {health}")
    else:
        # Handle unexpected data structures (e.g., list or error string).
        print(f"Unexpected response: {str(data)[:500]}")
        
except Exception as e:
    # Catch connection errors (e.g., server not running) or parsing errors.
    print(f"Exception: {e}")
