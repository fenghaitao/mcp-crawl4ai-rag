"""
Unit tests for GitService.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from core.services.git_service import GitService, GitInfo, GitRepositoryError


class TestGitService:
    """Test suite for GitService."""
    
    @pytest.fixture
    def git_service(self):
        """Create GitService instance."""
        return GitService()
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock git repository."""
        repo = Mock()
        repo.working_dir = "/path/to/repo"
        
        # Mock commit
        commit = Mock()
        commit.hexsha = "abc123def456"
        commit.committed_date = 1704067200  # 2024-01-01 00:00:00 UTC
        
        repo.head.commit = commit
        
        # Mock remotes
        origin = Mock()
        origin.url = "https://github.com/user/repo.git"
        repo.remotes = {'origin': origin}
        repo.remotes.origin = origin
        
        return repo
    
    def test_detect_repository_success(self, git_service, mock_repo):
        """Test successful repository detection."""
        with patch.object(git_service.git, 'Repo', return_value=mock_repo):
            file_path = Path("/path/to/repo/file.txt")
            git_info = git_service.detect_repository(file_path)
            
            assert git_info is not None
            assert git_info.repo_root == Path("/path/to/repo")
            assert git_info.repo_url == "https://github.com/user/repo.git"
            assert git_info.commit_sha == "abc123def456"
            assert isinstance(git_info.commit_timestamp, datetime)
    
    def test_detect_repository_not_found(self, git_service):
        """Test repository detection when no git repo exists."""
        with patch.object(git_service.git, 'Repo', side_effect=git_service.git.InvalidGitRepositoryError):
            file_path = Path("/path/to/non/repo/file.txt")
            git_info = git_service.detect_repository(file_path)
            
            assert git_info is None
    
    def test_detect_repository_error_handling(self, git_service):
        """Test repository detection with unexpected errors."""
        with patch.object(git_service.git, 'Repo', side_effect=Exception("Unexpected error")):
            file_path = Path("/path/to/file.txt")
            git_info = git_service.detect_repository(file_path)
            
            # Should return None on error, not raise
            assert git_info is None
    
    def test_get_commit_info_success(self, git_service, mock_repo):
        """Test getting commit information."""
        with patch.object(git_service.git, 'Repo', return_value=mock_repo):
            repo_root = Path("/path/to/repo")
            commit_sha, commit_timestamp = git_service.get_commit_info(repo_root)
            
            assert commit_sha == "abc123def456"
            assert isinstance(commit_timestamp, datetime)
            assert commit_timestamp.year == 2024
    
    def test_get_commit_info_error(self, git_service):
        """Test get_commit_info with error."""
        with patch.object(git_service.git, 'Repo', side_effect=Exception("Git error")):
            repo_root = Path("/path/to/repo")
            
            with pytest.raises(GitRepositoryError, match="Failed to get commit info"):
                git_service.get_commit_info(repo_root)
    
    def test_get_remote_url_with_origin(self, git_service, mock_repo):
        """Test getting remote URL when origin exists."""
        with patch.object(git_service.git, 'Repo', return_value=mock_repo):
            repo_root = Path("/path/to/repo")
            url = git_service.get_remote_url(repo_root)
            
            assert url == "https://github.com/user/repo.git"
    
    def test_get_remote_url_no_origin(self, git_service):
        """Test getting remote URL when origin doesn't exist but other remotes do."""
        repo = Mock()
        repo.working_dir = "/path/to/repo"
        
        # Mock remotes without origin
        upstream = Mock()
        upstream.url = "https://github.com/upstream/repo.git"
        repo.remotes = [upstream]
        
        with patch.object(git_service.git, 'Repo', return_value=repo):
            repo_root = Path("/path/to/repo")
            url = git_service.get_remote_url(repo_root)
            
            assert url == "https://github.com/upstream/repo.git"
    
    def test_get_remote_url_no_remotes(self, git_service):
        """Test getting remote URL when no remotes configured."""
        repo = Mock()
        repo.working_dir = "/path/to/repo"
        repo.remotes = []
        
        with patch.object(git_service.git, 'Repo', return_value=repo):
            repo_root = Path("/path/to/repo")
            url = git_service.get_remote_url(repo_root)
            
            # Should fall back to file:// URL
            assert url.startswith("file://")
            assert "repo" in url
    
    def test_get_remote_url_error(self, git_service):
        """Test get_remote_url with error."""
        with patch.object(git_service.git, 'Repo', side_effect=Exception("Git error")):
            repo_root = Path("/path/to/repo")
            
            with pytest.raises(GitRepositoryError, match="Failed to get remote URL"):
                git_service.get_remote_url(repo_root)
    
    def test_get_relative_path_success(self, git_service):
        """Test getting relative path."""
        repo_root = Path("/path/to/repo")
        file_path = Path("/path/to/repo/src/file.py")
        
        relative_path = git_service.get_relative_path(repo_root, file_path)
        
        assert relative_path == "src/file.py"
    
    def test_get_relative_path_file_outside_repo(self, git_service):
        """Test getting relative path for file outside repository."""
        repo_root = Path("/path/to/repo")
        file_path = Path("/other/path/file.py")
        
        with pytest.raises(GitRepositoryError, match="not within repository"):
            git_service.get_relative_path(repo_root, file_path)
    
    def test_git_info_get_relative_path(self):
        """Test GitInfo.get_relative_path method."""
        git_info = GitInfo(
            repo_root=Path("/path/to/repo"),
            repo_url="https://github.com/user/repo.git",
            commit_sha="abc123",
            commit_timestamp=datetime.now()
        )
        
        file_path = Path("/path/to/repo/docs/readme.md")
        relative_path = git_info.get_relative_path(file_path)
        
        assert relative_path == "docs/readme.md"
    
    def test_git_service_requires_gitpython(self):
        """Test that GitService raises error if GitPython not installed."""
        with patch('core.services.git_service.GitService.__init__', side_effect=ImportError("GitPython required")):
            with pytest.raises(ImportError, match="GitPython"):
                GitService()
