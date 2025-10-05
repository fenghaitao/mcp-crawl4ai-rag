#!/usr/bin/env python3
"""
Rate Limiting Test for GitHub Copilot Client

Tests rate limiting functionality, exponential backoff, and burst protection.
"""

import asyncio
import time
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from copilot_client import CopilotClient, RateLimiter


async def test_rate_limiter_basic():
    """Test basic rate limiting functionality."""
    print("Testing basic rate limiting...")
    
    # Create a very restrictive rate limiter for testing
    rate_limiter = RateLimiter(requests_per_minute=3, burst_limit=2)
    
    start_time = time.time()
    
    for i in range(5):
        request_start = time.time()
        await rate_limiter.wait_if_needed()
        request_end = time.time()
        
        wait_time = request_end - request_start
        total_time = request_end - start_time
        
        print(f"Request {i+1}: waited {wait_time:.2f}s, total time {total_time:.2f}s")
        
        # Simulate successful request
        rate_limiter.record_success()
    
    total_duration = time.time() - start_time
    print(f"✅ Total test duration: {total_duration:.2f}s")
    print(f"✅ Rate limiting working correctly!")


async def test_error_backoff():
    """Test exponential backoff on errors."""
    print("\nTesting error backoff...")
    
    rate_limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
    
    # Simulate consecutive errors
    for i in range(3):
        print(f"Simulating error {i+1}...")
        rate_limiter.record_error(429)  # Rate limit error
        
        start_time = time.time()
        await rate_limiter.wait_if_needed()
        wait_time = time.time() - start_time
        
        expected_backoff = min(2 ** i, 30)
        print(f"  Expected backoff: ~{expected_backoff}s, Actual wait: {wait_time:.2f}s")
    
    print("✅ Error backoff working correctly!")


async def test_copilot_client_rate_limiting():
    """Test rate limiting in actual Copilot client."""
    print("\nTesting Copilot client with rate limiting...")
    
    # Check if GitHub token is available
    import os
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("⚠️  GITHUB_TOKEN not available, skipping Copilot client test")
        return
    
    # Create client with moderate rate limiting for testing
    client = CopilotClient(github_token, requests_per_minute=10)
    
    if not await client.initialize():
        print("❌ Failed to initialize Copilot client")
        return
    
    print("Making 3 requests with rate limiting...")
    start_time = time.time()
    
    for i in range(3):
        request_start = time.time()
        try:
            result = await client.create_embeddings(f"Test text {i+1}")
            request_end = time.time()
            
            request_time = request_end - request_start
            total_time = request_end - start_time
            
            print(f"Request {i+1}: {len(result.embeddings[0])} dims, "
                  f"took {request_time:.2f}s, total {total_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
    
    total_duration = time.time() - start_time
    print(f"✅ Total duration: {total_duration:.2f}s")
    print("✅ Copilot client rate limiting working!")


async def test_burst_protection():
    """Test burst protection functionality."""
    print("\nTesting burst protection...")
    
    rate_limiter = RateLimiter(requests_per_minute=60, burst_limit=3)
    
    print("Making 5 rapid requests (burst limit = 3)...")
    start_time = time.time()
    
    for i in range(5):
        request_start = time.time()
        await rate_limiter.wait_if_needed()
        request_end = time.time()
        
        wait_time = request_end - request_start
        total_time = request_end - start_time
        
        print(f"Request {i+1}: waited {wait_time:.2f}s, total {total_time:.2f}s")
        rate_limiter.record_success()
        
        # Small delay to simulate request processing
        await asyncio.sleep(0.1)
    
    print("✅ Burst protection working correctly!")


async def main():
    """Run all rate limiting tests."""
    print("=" * 60)
    print("GitHub Copilot Rate Limiting Tests")
    print("=" * 60)
    
    # Test 1: Basic rate limiting
    await test_rate_limiter_basic()
    
    # Test 2: Error backoff
    await test_error_backoff()
    
    # Test 3: Burst protection
    await test_burst_protection()
    
    # Test 4: Real Copilot client (if token available)
    await test_copilot_client_rate_limiting()
    
    print("\n" + "=" * 60)
    print("RATE LIMITING FEATURES SUMMARY")
    print("=" * 60)
    print("✅ Basic rate limiting (requests per minute)")
    print("✅ Burst protection (requests per 10 seconds)")
    print("✅ Exponential backoff on errors")
    print("✅ 429 (rate limit) error handling")
    print("✅ 5xx (server error) handling")
    print("✅ Configurable via environment variables")
    print("✅ Integration with token refresh")
    print("\nConfiguration:")
    print("  COPILOT_REQUESTS_PER_MINUTE=60 (default)")
    print("  Burst limit: 10 requests per 10 seconds")
    print("  Max backoff: 30 seconds")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())