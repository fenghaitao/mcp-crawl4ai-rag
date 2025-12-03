#!/usr/bin/env python3
"""
Progress Tracker for Simics Source Code Crawling
Provides persistent storage of file processing status with checkboxes.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from filelock import FileLock
import logging


class ProgressTracker:
    """
    Tracks progress of file processing with persistent storage.
    
    Each file has:
    - name: The file path
    - completed: Boolean checkbox indicating if all 5 steps are done
    - steps_completed: List of completed step names
    - last_updated: Timestamp of last update
    - error: Optional error message if processing failed
    """
    
    def __init__(self, progress_file: str = "progress/simics_crawl_progress.json"):
        """
        Initialize progress tracker.
        
        Args:
            progress_file: Path to the JSON file storing progress
        """
        self.progress_file = Path(progress_file)
        self.lock_file = Path(str(self.progress_file) + ".lock")
        self.progress_data: Dict[str, Dict] = {}
        
        # Create progress directory if it doesn't exist
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing progress
        self._load_progress()
    
    def _load_progress(self):
        """Load progress from JSON file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.progress_data = json.load(f)
                logging.info(f"📂 Loaded progress: {len(self.progress_data)} files tracked")
            except Exception as e:
                logging.warning(f"⚠️  Failed to load progress file: {e}")
                self.progress_data = {}
        else:
            logging.info(f"📝 Creating new progress file: {self.progress_file}")
            self.progress_data = {}
    
    def _save_progress(self):
        """Save progress to JSON file with file locking."""
        try:
            # Use file lock to prevent concurrent writes
            lock = FileLock(self.lock_file, timeout=10)
            with lock:
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"❌ Failed to save progress: {e}")
    
    def add_file(self, file_path: str):
        """
        Add a file to the tracker if not already present.
        
        Args:
            file_path: Path to the file
        """
        if file_path not in self.progress_data:
            self.progress_data[file_path] = {
                "name": file_path,
                "completed": False,
                "steps_completed": [],
                "total_steps": 5,
                "added_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "error": None,
                "chunks_created": 0,
                "chunks_uploaded": 0
            }
            self._save_progress()
    
    def add_files(self, file_paths: List[str]):
        """
        Add multiple files to the tracker.
        
        Args:
            file_paths: List of file paths
        """
        added = 0
        for file_path in file_paths:
            if file_path not in self.progress_data:
                self.progress_data[file_path] = {
                    "name": file_path,
                    "completed": False,
                    "steps_completed": [],
                    "total_steps": 5,
                    "added_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "error": None,
                    "chunks_created": 0,
                    "chunks_uploaded": 0
                }
                added += 1
        
        if added > 0:
            self._save_progress()
            logging.info(f"➕ Added {added} new files to progress tracker")
    
    def mark_step_completed(self, file_path: str, step_name: str):
        """
        Mark a processing step as completed for a file.
        
        Args:
            file_path: Path to the file
            step_name: Name of the completed step (e.g., "file_summary", "chunking")
        """
        if file_path not in self.progress_data:
            self.add_file(file_path)
        
        file_data = self.progress_data[file_path]
        if step_name not in file_data["steps_completed"]:
            file_data["steps_completed"].append(step_name)
            file_data["last_updated"] = datetime.now().isoformat()
            self._save_progress()
    
    def mark_completed(self, file_path: str, chunks_created: int = 0, chunks_uploaded: int = 0):
        """
        Mark a file as fully completed (all 5 steps done).
        
        Args:
            file_path: Path to the file
            chunks_created: Number of chunks created
            chunks_uploaded: Number of chunks uploaded
        """
        if file_path not in self.progress_data:
            self.add_file(file_path)
        
        self.progress_data[file_path]["completed"] = True
        self.progress_data[file_path]["chunks_created"] = chunks_created
        self.progress_data[file_path]["chunks_uploaded"] = chunks_uploaded
        self.progress_data[file_path]["completed_at"] = datetime.now().isoformat()
        self.progress_data[file_path]["last_updated"] = datetime.now().isoformat()
        self.progress_data[file_path]["error"] = None
        
        # Ensure all steps are marked
        expected_steps = ["file_summary", "chunking", "chunk_summaries", "prepare_embedding", "upload"]
        for step in expected_steps:
            if step not in self.progress_data[file_path]["steps_completed"]:
                self.progress_data[file_path]["steps_completed"].append(step)
        
        self._save_progress()
    
    def mark_failed(self, file_path: str, error: str):
        """
        Mark a file as failed with error message.
        
        Args:
            file_path: Path to the file
            error: Error message
        """
        if file_path not in self.progress_data:
            self.add_file(file_path)
        
        self.progress_data[file_path]["completed"] = False
        self.progress_data[file_path]["error"] = error
        self.progress_data[file_path]["failed_at"] = datetime.now().isoformat()
        self.progress_data[file_path]["last_updated"] = datetime.now().isoformat()
        self._save_progress()
    
    def is_completed(self, file_path: str) -> bool:
        """
        Check if a file is marked as completed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if completed, False otherwise
        """
        return self.progress_data.get(file_path, {}).get("completed", False)
    
    def get_completed_files(self) -> Set[str]:
        """
        Get set of all completed file paths.
        
        Returns:
            Set of completed file paths
        """
        return {path for path, data in self.progress_data.items() if data.get("completed", False)}
    
    def get_pending_files(self) -> Set[str]:
        """
        Get set of all pending (not completed) file paths.
        
        Returns:
            Set of pending file paths
        """
        return {path for path, data in self.progress_data.items() if not data.get("completed", False)}
    
    def get_failed_files(self) -> Set[str]:
        """
        Get set of all failed file paths.
        
        Returns:
            Set of failed file paths
        """
        return {path for path, data in self.progress_data.items() if data.get("error") is not None}
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the progress.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.progress_data)
        completed = len(self.get_completed_files())
        pending = len(self.get_pending_files())
        failed = len(self.get_failed_files())
        
        total_chunks_created = sum(data.get("chunks_created", 0) for data in self.progress_data.values())
        total_chunks_uploaded = sum(data.get("chunks_uploaded", 0) for data in self.progress_data.values())
        
        return {
            "total_files": total,
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "completion_rate": f"{(completed / total * 100):.1f}%" if total > 0 else "0%",
            "total_chunks_created": total_chunks_created,
            "total_chunks_uploaded": total_chunks_uploaded
        }
    
    def print_summary(self):
        """Print a summary of the progress."""
        stats = self.get_statistics()
        
        print(f"\n{'='*60}")
        print(f"📊 Progress Summary")
        print(f"{'='*60}")
        print(f"   Total Files:      {stats['total_files']}")
        print(f"   ✅ Completed:     {stats['completed']} ({stats['completion_rate']})")
        print(f"   ⏳ Pending:       {stats['pending']}")
        print(f"   ❌ Failed:        {stats['failed']}")
        print(f"   📦 Chunks Created: {stats['total_chunks_created']}")
        print(f"   💾 Chunks Uploaded: {stats['total_chunks_uploaded']}")
        print(f"{'='*60}\n")
    
    def reset_failed_files(self):
        """Reset all failed files to pending status."""
        count = 0
        for path, data in self.progress_data.items():
            if data.get("error") is not None:
                data["error"] = None
                data["completed"] = False
                data["steps_completed"] = []
                data["last_updated"] = datetime.now().isoformat()
                count += 1
        
        if count > 0:
            self._save_progress()
            logging.info(f"♻️  Reset {count} failed files to pending status")
    
    def reset_all(self):
        """Reset all files to pending status."""
        self.progress_data = {}
        self._save_progress()
        logging.info(f"♻️  Reset all progress data")
    
    def clear(self):
        """
        Clear all progress data and delete the progress file.
        This completely removes all tracking information.
        """
        self.progress_data = {}
        
        # Delete the progress file
        if self.progress_file.exists():
            try:
                self.progress_file.unlink()
                logging.info(f"🗑️  Deleted progress file: {self.progress_file}")
            except Exception as e:
                logging.error(f"❌ Failed to delete progress file: {e}")
        
        # Delete the lock file if it exists
        if self.lock_file.exists():
            try:
                self.lock_file.unlink()
                logging.info(f"🗑️  Deleted lock file: {self.lock_file}")
            except Exception as e:
                logging.error(f"❌ Failed to delete lock file: {e}")
        
        logging.info(f"✨ Cleared all progress data")
    
    def export_checklist(self, output_file: str = "progress/checklist.txt"):
        """
        Export a human-readable checklist.
        
        Args:
            output_file: Path to output file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Simics Source Code Crawling Checklist\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"{'='*80}\n\n")
            
            stats = self.get_statistics()
            f.write(f"Progress: {stats['completed']}/{stats['total_files']} ({stats['completion_rate']})\n\n")
            
            # Group by status
            completed_files = sorted(self.get_completed_files())
            pending_files = sorted(self.get_pending_files())
            failed_files = sorted(self.get_failed_files())
            
            if completed_files:
                f.write(f"\n✅ COMPLETED ({len(completed_files)} files)\n")
                f.write(f"{'-'*80}\n")
                for path in completed_files:
                    data = self.progress_data[path]
                    chunks = data.get("chunks_uploaded", 0)
                    f.write(f"[✓] {Path(path).name} ({chunks} chunks)\n")
            
            if pending_files:
                f.write(f"\n⏳ PENDING ({len(pending_files)} files)\n")
                f.write(f"{'-'*80}\n")
                for path in pending_files:
                    if path not in failed_files:  # Exclude failed from pending
                        f.write(f"[ ] {Path(path).name}\n")
            
            if failed_files:
                f.write(f"\n❌ FAILED ({len(failed_files)} files)\n")
                f.write(f"{'-'*80}\n")
                for path in failed_files:
                    data = self.progress_data[path]
                    error = data.get("error", "Unknown error")
                    f.write(f"[✗] {Path(path).name}\n")
                    f.write(f"    Error: {error}\n\n")
        
        logging.info(f"📋 Exported checklist to: {output_path}")
