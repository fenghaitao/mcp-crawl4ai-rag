#!/usr/bin/env python3
"""
Sample Python script to test hallucination detection.
"""

import requests
import json

def fetch_user_data(user_id):
    """Fetch user data from an API."""
    # This is a real requests method
    response = requests.get(f"https://api.example.com/users/{user_id}")
    
    # This would be a hallucination if requests doesn't have this method
    # response.magical_parse()  # This would be detected as a hallucination
    
    return response.json()

def process_data(data):
    """Process the fetched data."""
    # Real json method
    result = json.dumps(data, indent=2)
    return result

if __name__ == "__main__":
    # This is valid code using real methods
    user_data = fetch_user_data(123)
    processed = process_data(user_data)
    print(processed)
