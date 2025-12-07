"""
Git repository service for detecting and extracting repository information.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class GitInfo:
    """Git repository information."""
    repo_root: Path
    repo_url: str
    commit_sha: str
    commit_timestamp: datetime
    
    def get_relative_path(self, file_path: Path) -> str:
        """Get path relative to repository root."""
        return str(file_path.relative_to(self.repo_root))


class GitRepositoryError(Exception):
    """Raised when git operations fail."""
    pass


class GitService:
    """Service for git repository operations."""
    
    def __init__(self):
        """Initialize GitService."""
        try:
            import git
            self.git = git
        except ImportError:
            raise ImportError(
                "GitPython is required for git operations. "
                "Install it with: pip install gitpython"
            )
    
    def detect_repository(self, file_path: Path) -> Optional[GitInfo]:
        """
        Detect git repository for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            GitInfo if file is in a git repository, None otherwise
        """
        try:
            # Search for git repository starting from file's directory
            search_path = file_path if file_path.is_dir() else file_path.parent
            repo = self.git.Repo(search_path, search_parent_directories=True)
            
            # Get commit information
            commit_sha, commit_timestamp = self.get_commit_info(Path(repo.working_dir))
            
            # Get remote URL
            repo_url = self.get_remote_url(Path(repo.working_dir))
            
            return GitInfo(
                repo_root=Path(repo.working_dir),
                repo_url=repo_url,
                commit_sha=commit_sha,
                commit_timestamp=commit_timestamp
            )
            
        except self.git.InvalidGitRepositoryError:
            logger.debug(f"No git repository found for {file_path}")
            return None
        except Exception as e:
            logger.warning(f"Error detecting git repository for {file_path}: {e}")
            return None
    
    def get_commit_info(self, repo_root: Path) -> tuple[str, datetime]:
        """
        Get current commit SHA and timestamp.
        
        Args:
            repo_root: Path to repository root
            
        Returns:
            Tuple of (commit_sha, commit_timestamp)
            
        Raises:
            GitRepositoryError: If unable to get commit information
        """
        try:
            repo = self.git.Repo(repo_root)
            commit = repo.head.commit
            
            commit_sha = commit.hexsha
            commit_timestamp = datetime.fromtimestamp(commit.committed_date)
            
            return commit_sha, commit_timestamp
            
        except Exception as e:
            raise GitRepositoryError(f"Failed to get commit info: {e}")
    
    def get_remote_url(self, repo_root: Path) -> str:
        """
        Get git remote URL.
        
        Args:
            repo_root: Path to repository root
            
        Returns:
            Remote URL (e.g., https://github.com/user/repo.git)
            
        Raises:
            GitRepositoryError: If unable to get remote URL
        """
        try:
            repo = self.git.Repo(repo_root)
            
            # Try to get origin remote
            if 'origin' in repo.remotes:
                return repo.remotes.origin.url
            
            # Fall back to first available remote
            if repo.remotes:
                return repo.remotes[0].url
            
            # No remotes configured - use local path
            logger.warning(f"No git remotes configured for {repo_root}")
            return f"file://{repo_root.absolute()}"
            
        except Exception as e:
            raise GitRepositoryError(f"Failed to get remote URL: {e}")
    
    def get_relative_path(self, repo_root: Path, file_path: Path) -> str:
        """
        Get file path relative to repository root.
        
        Args:
            repo_root: Path to repository root
            file_path: Path to file
            
        Returns:
            Relative path as string
            
        Raises:
            GitRepositoryError: If file is not within repository
        """
        try:
            return str(file_path.relative_to(repo_root))
        except ValueError as e:
            raise GitRepositoryError(
                f"File {file_path} is not within repository {repo_root}: {e}"
            )
