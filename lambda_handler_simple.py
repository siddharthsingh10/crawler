import json
import urllib.request
import urllib.parse
import re
import time
import os
from typing import Dict, Optional, List
from urllib.parse import urlparse
import html.parser
import html.entities

def _cors_headers() -> Dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Api-Key",
        "Content-Type": "application/json",
    }

def _bad_request(message: str, status_code: int = 400) -> Dict:
    return {"statusCode": status_code, "headers": _cors_headers(), "body": json.dumps({"error": message})}

def _unauthorized(message: str = "Unauthorized") -> Dict:
    return {"statusCode": 401, "headers": _cors_headers(), "body": json.dumps({"error": message})}

def validate_api_key(event: Dict) -> bool:
    """Validate API key from headers or query parameters"""
    # Get API key from environment variable
    expected_api_key = os.environ.get('API_KEY')
    print(f"Expected API key: {expected_api_key}")
    
    if not expected_api_key:
        print("Warning: No API_KEY environment variable set")
        return True  # Allow if no key is configured
    
    # Check headers first
    headers = event.get('headers', {}) or {}
    print(f"Headers: {headers}")
    api_key = headers.get('X-Api-Key') or headers.get('x-api-key')
    print(f"API key from headers: {api_key}")
    
    # If not in headers, check query parameters
    if not api_key:
        params = event.get('queryStringParameters') or {}
        print(f"Query params: {params}")
        api_key = params.get('api_key') if isinstance(params, dict) else None
        print(f"API key from query params: {api_key}")
    
    # Validate the key
    if not api_key or api_key != expected_api_key:
        print(f"API key validation failed. Expected: {expected_api_key}, Got: {api_key}")
        return False
    
    print("API key validation successful")
    return True

def fetch_url_simple(url: str) -> Optional[str]:
    """Fetch URL using built-in urllib"""
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_metadata_simple(html_content: str, url: str) -> Dict:
    """Extract metadata using basic string operations"""
    
    # Extract title
    title = ""
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    
    # Extract description
    description = ""
    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    if desc_match:
        description = desc_match.group(1).strip()
    
    # Extract body content (simplified)
    body = ""
    # Remove script and style tags
    body_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
    body_content = re.sub(r'<style[^>]*>.*?</style>', '', body_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Extract text from body
    body_text = re.sub(r'<[^>]+>', ' ', body_content)
    body_text = re.sub(r'\s+', ' ', body_text).strip()
    body = body_text[:2000]  # Limit to 2000 characters
    
    # Simple topic classification
    topics = []
    content_lower = f"{title} {description} {body}".lower()
    
    if any(word in content_lower for word in ['buy', 'price', 'sale', 'product', 'shopping']):
        topics.append('e-commerce')
    if any(word in content_lower for word in ['news', 'breaking', 'report']):
        topics.append('news')
    if any(word in content_lower for word in ['blog', 'post', 'article']):
        topics.append('blog')
    if any(word in content_lower for word in ['technology', 'software', 'app']):
        topics.append('technology')
    
    if not topics:
        topics.append('general')
    
    return {
        'url': url,
        'title': title,
        'description': description,
        'body': body,
        'topics': topics,
        'extracted_at': time.time()
    }

def handler(event: Dict, context=None) -> Dict:
    """AWS Lambda handler"""
    
    # Handle OPTIONS for CORS
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps({"ok": True})}
    
    # Validate API key
    if not validate_api_key(event):
        return _unauthorized("Invalid or missing API key")
    
    # Get URL parameter
    params = (event.get("queryStringParameters") or {})
    url = params.get("url") if isinstance(params, dict) else None
    
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return _bad_request("Missing or invalid 'url' query parameter")
    
    try:
        # Fetch the URL
        html_content = fetch_url_simple(url)
        if not html_content:
            return _bad_request("Failed to fetch the provided URL", status_code=502)
        
        # Extract metadata
        result = extract_metadata_simple(html_content, url)
        
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(result, default=str)}
        
    except Exception as e:
        print(f"Error processing request: {e}")
        return _bad_request("Internal server error", status_code=500)
