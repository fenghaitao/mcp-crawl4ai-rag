#!/usr/bin/env python3
"""
Install all project dependencies without sudo permission.
This script reads dependencies from pyproject.toml and installs them using uv pip,
then sets up Playwright and other crawl4ai dependencies.
"""
import subprocess
import sys
import os

dependencies = [
    "crawl4ai==0.6.2",
    "mcp==1.7.1",
    "supabase==2.15.1",
    "openai==1.71.0",
    "dotenv==0.9.9",
    "sentence-transformers>=4.1.0",
    "neo4j>=5.28.1",
    "httpx>=0.25.0",
    "aiofiles>=23.0.0",
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]

def install_packages(packages):
    """Install packages using uv pip without sudo."""
    print(f"Installing {len(packages)} packages...")
    for i, package in enumerate(packages, 1):
        print(f"\n[{i}/{len(packages)}] Installing {package}...")
        try:
            subprocess.check_call(["uv", "pip", "install", package])
            print(f"✓ Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    return True

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
    print("Installing project dependencies (without sudo)")
    print("=" * 70)
    
    # Step 1: Install Python packages
    success = install_packages(dependencies)
    if not success:
        print("\n" + "=" * 70)
        print("✗ Python package installation failed")
        print("=" * 70)
        sys.exit(1)
    
    # Step 2: Install Playwright browsers
    print("\n" + "=" * 70)
    print("Step 2: Installing Playwright")
    print("=" * 70)
    playwright_success = install_playwright()
    
    # Step 3: Run crawl4ai setup
    print("\n" + "=" * 70)
    print("Step 3: Running crawl4ai setup")
    print("=" * 70)
    crawl4ai_success = run_crawl4ai_setup()
    
    # Final summary
    print("\n" + "=" * 70)
    print("Installation Summary")
    print("=" * 70)
    print(f"Python packages: {'✓ Success' if success else '✗ Failed'}")
    print(f"Playwright: {'✓ Success' if playwright_success else '✗ Failed'}")
    print(f"Crawl4ai setup: {'✓ Success' if crawl4ai_success else '✗ Failed'}")
    
    if success and playwright_success and crawl4ai_success:
        print("\n✓ All installations completed successfully!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n⚠️  Some installations had issues. Check messages above.")
        print("=" * 70)
        sys.exit(1)
