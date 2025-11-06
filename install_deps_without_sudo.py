#!/usr/bin/env python3
"""
Post-installation setup for crawl4ai dependencies without sudo permission.
This script should be run AFTER installing Python packages with 'uv pip install'.
It handles Playwright browser installation and crawl4ai post-installation setup.
"""
import subprocess
import sys
import os

def install_playwright():
    """Install Playwright browsers (chromium) without sudo."""
    print("\nInstalling Playwright browsers...")
    try:
        # Install playwright package if not already installed
        subprocess.check_call(["uv", "pip", "install", "playwright"])
        print("✓ Playwright package installed")
        
        # Install chromium browser without system dependencies (no sudo)
        print("\nInstalling Chromium browser (this may take a while)...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✓ Chromium browser installed")
        
        print("\n⚠️  Note: System dependencies for Playwright were NOT installed (requires sudo).")
        print("   If you encounter issues, you may need to install them manually:")
        print(f"   sudo {sys.executable} -m playwright install-deps chromium")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Playwright: {e}")
        return False

def run_crawl4ai_setup():
    """Run the crawl4ai post-installation setup."""
    print("\nRunning crawl4ai-setup...")
    try:
        # Set environment variable to skip system dependencies installation
        env = os.environ.copy()
        subprocess.check_call([sys.executable, "-m", "crawl4ai.install"], env=env)
        print("✓ crawl4ai setup completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to run crawl4ai setup: {e}")
        print("   You can run it manually later: crawl4ai-setup")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during crawl4ai setup: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Post-installation setup for crawl4ai (without sudo)")
    print("=" * 70)
    print("Note: This assumes Python packages are already installed via 'uv pip install'")
    print("=" * 70)
    
    # Step 1: Install Playwright browsers
    print("\nStep 1: Installing Playwright browsers")
    print("=" * 70)
    playwright_success = install_playwright()
    
    # Step 2: Run crawl4ai setup
    print("\n" + "=" * 70)
    print("Step 2: Running crawl4ai setup")
    print("=" * 70)
    crawl4ai_success = run_crawl4ai_setup()
    
    # Final summary
    print("\n" + "=" * 70)
    print("Post-installation Summary")
    print("=" * 70)
    print(f"Playwright browsers: {'✓ Success' if playwright_success else '✗ Failed'}")
    print(f"Crawl4ai setup: {'✓ Success' if crawl4ai_success else '✗ Failed'}")
    
    if playwright_success and crawl4ai_success:
        print("\n✓ All post-installation steps completed successfully!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n⚠️  Some post-installation steps had issues. Check messages above.")
        print("=" * 70)
        sys.exit(1)
