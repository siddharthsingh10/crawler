"""
Test script for the web crawler functionality.
Tests the crawler with the provided assignment URLs and working demo URLs.
"""

import json
import time
from crawler.core import WebCrawler

def test_crawler():
    """
    Test the crawler with the provided assignment URLs and working demo URLs.
    """
    # Test URLs from the assignment (may be blocked)
    assignment_urls = [
        "http://www.amazon.com/Cuisinart-CPT-122-Compact-2-Slice-Toaster/dp/B009GQ034C",
        "http://blog.rei.com/camp/how-to-introduce-your-indoorsy-friend-to-the-outdoors/",
        "http://www.cnn.com/2013/06/10/politics/edward-snowden-profile/"
    ]
    
    # Working demo URLs for testing functionality
    demo_urls = [
        "https://httpbin.org/html",
        "https://example.com",
        "https://httpbin.org/json"
    ]
    
    # Initialize crawler
    crawler = WebCrawler(timeout=30, max_retries=3, delay=1.0)
    
    print("🚀 Starting Web Crawler Test")
    print("=" * 50)
    
    # Test assignment URLs first
    print("\n📋 Testing Assignment URLs (may be blocked):")
    print("-" * 40)
    assignment_results = test_urls(crawler, assignment_urls, "Assignment")
    
    # Test demo URLs
    print("\n📋 Testing Demo URLs (should work):")
    print("-" * 40)
    demo_results = test_urls(crawler, demo_urls, "Demo")
    
    # Combine results
    all_results = {**assignment_results, **demo_results}
    
    # Save results to file
    with open('crawler_test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("\n" + "=" * 50)
    print("📊 Final Test Summary:")
    print(f"✅ Successful crawls: {sum(1 for r in all_results.values() if r is not None)}/{len(all_results)}")
    print(f"❌ Failed crawls: {sum(1 for r in all_results.values() if r is None)}/{len(all_results)}")
    print("💾 Results saved to: crawler_test_results.json")
    
    return all_results

def test_urls(crawler, urls, test_type):
    """
    Test a list of URLs and return results.
    
    Args:
        crawler: WebCrawler instance
        urls: List of URLs to test
        test_type: Type of test (for logging)
        
    Returns:
        Dictionary of results
    """
    results = {}
    
    for i, url in enumerate(urls, 1):
        print(f"\n📄 Testing {test_type} URL {i}/{len(urls)}: {url}")
        print("-" * 40)
        
        try:
            # Crawl the URL
            start_time = time.time()
            result = crawler.crawl(url)
            end_time = time.time()
            
            if result:
                print(f"✅ Successfully crawled in {end_time - start_time:.2f}s")
                print(f"📝 Title: {result['title'][:100]}...")
                print(f"📄 Description: {result['description'][:100]}...")
                print(f"🏷️  Topics: {', '.join(result['topics'])}")
                print(f"📊 Body length: {len(result['body'])} characters")
                
                results[url] = result
            else:
                print(f"❌ Failed to crawl URL")
                results[url] = None
                
        except Exception as e:
            print(f"❌ Error testing URL: {e}")
            results[url] = None
            
        # Add delay between requests
        if i < len(urls):
            print("⏳ Waiting 2 seconds before next request...")
            time.sleep(2)
    
    return results

if __name__ == "__main__":
    test_crawler() 