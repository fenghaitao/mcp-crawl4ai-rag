#!/usr/bin/env python3
"""
Test the Progress Tracker functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from progress_tracker import ProgressTracker

def test_progress_tracker():
    """Test basic progress tracker functionality."""
    print("🧪 Testing Progress Tracker\n")
    
    # Create tracker with test file
    tracker = ProgressTracker(progress_file="progress/test_progress.json")
    
    # Test 1: Add files
    print("Test 1: Adding files...")
    test_files = [
        "test_files/device1.dml",
        "test_files/device2.dml",
        "test_files/utils.py",
        "test_files/interface.py"
    ]
    tracker.add_files(test_files)
    print(f"✅ Added {len(test_files)} files\n")
    
    # Test 2: Mark steps completed
    print("Test 2: Processing file through 5 steps...")
    file = test_files[0]
    steps = ["file_summary", "chunking", "chunk_summaries", "prepare_embedding", "upload"]
    
    for i, step in enumerate(steps, 1):
        tracker.mark_step_completed(file, step)
        print(f"   Step {i}/5: {step} ✓")
    
    # Mark as completed
    tracker.mark_completed(file, chunks_created=10, chunks_uploaded=10)
    print(f"✅ File marked as completed\n")
    
    # Test 3: Check completion status
    print("Test 3: Checking completion status...")
    if tracker.is_completed(file):
        print(f"✅ {file} is completed\n")
    else:
        print(f"❌ {file} is NOT completed\n")
    
    # Test 4: Mark a file as failed
    print("Test 4: Marking file as failed...")
    failed_file = test_files[1]
    tracker.mark_failed(failed_file, "Test error: Simulated failure")
    print(f"✅ {failed_file} marked as failed\n")
    
    # Test 5: Get statistics
    print("Test 5: Getting statistics...")
    tracker.print_summary()
    
    # Test 6: Export checklist
    print("Test 6: Exporting checklist...")
    tracker.export_checklist("progress/test_checklist.txt")
    print(f"✅ Checklist exported to progress/test_checklist.txt\n")
    
    # Test 7: Get specific sets
    print("Test 7: Getting file sets...")
    completed = tracker.get_completed_files()
    pending = tracker.get_pending_files()
    failed = tracker.get_failed_files()
    
    print(f"   Completed files: {len(completed)}")
    print(f"   Pending files: {len(pending)}")
    print(f"   Failed files: {len(failed)}\n")
    
    # Show checklist content
    print("="*60)
    print("📋 Generated Checklist Preview:")
    print("="*60)
    with open("progress/test_checklist.txt", 'r') as f:
        content = f.read()
        # Show first 40 lines
        lines = content.split('\n')[:40]
        print('\n'.join(lines))
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_progress_tracker()
