"""
Integration tests for batch processing and query system.

Tests end-to-end workflows including:
- Batch ingestion with git integration
- Temporal queries
- File history tracking
- Resume capability
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import time


@pytest.fixture
def test_git_repo(tmp_path):
    """Create a test git repository with sample files."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git repo
    subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_dir, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_dir, check=True)
    
    # Create initial files
    (repo_dir / "README.md").write_text("# Test Repository\n\nInitial content.")
    (repo_dir / "docs").mkdir()
    (repo_dir / "docs" / "guide.md").write_text("# User Guide\n\nVersion 1 content.")
    
    # First commit
    subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_dir, check=True)
    
    # Wait a moment to ensure different timestamps
    time.sleep(0.1)
    
    # Update files for second commit
    (repo_dir / "docs" / "guide.md").write_text("# User Guide\n\nVersion 2 content with updates.")
    (repo_dir / "docs" / "api.md").write_text("# API Reference\n\nNew API documentation.")
    
    # Second commit
    subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
    subprocess.run(['git', 'commit', '-m', 'Update documentation'], cwd=repo_dir, check=True)
    
    yield repo_dir
    
    # Cleanup
    shutil.rmtree(repo_dir, ignore_errors=True)


@pytest.fixture
def mock_backend():
    """Create a mock backend for testing."""
    from tests.unit.test_query_service import MockBackend
    return MockBackend()


class TestEndToEndBatchIngestion:
    """Test end-to-end batch ingestion workflows."""
    
    def test_batch_ingest_with_git_integration(self, test_git_repo, mock_backend):
        """Test batch ingestion with git repository detection."""
        from core.services.git_service import GitService
        from core.services.document_ingest_service import DocumentIngestService
        from core.services.batch_ingest_service import BatchIngestService
        
        # Create services
        git_service = GitService()
        ingest_service = DocumentIngestService(mock_backend, git_service)
        batch_service = BatchIngestService(mock_backend, git_service, ingest_service)
        
        # Run batch ingestion
        progress = batch_service.ingest_batch(
            directory=test_git_repo,
            pattern="*.md",
            recursive=True,
            force=False,
            dry_run=False,
            resume=False
        )
        
        # Verify results
        assert progress.total_files == 3  # README.md, guide.md, api.md
        assert progress.succeeded == 3
        assert progress.failed == 0
        
        # Verify files were stored with git info
        assert len(mock_backend.files) == 3
        for file in mock_backend.files:
            assert file['commit_sha'] is not None
            assert file['valid_from'] is not None
    
    def test_batch_ingest_dry_run(self, test_git_repo, mock_backend):
        """Test batch ingestion in dry-run mode."""
        from core.services.git_service import GitService
        from core.services.document_ingest_service import DocumentIngestService
        from core.services.batch_ingest_service import BatchIngestService
        
        git_service = GitService()
        ingest_service = DocumentIngestService(mock_backend, git_service)
        batch_service = BatchIngestService(mock_backend, git_service, ingest_service)
        
        # Run dry-run
        progress = batch_service.ingest_batch(
            directory=test_git_repo,
            pattern="*.md",
            recursive=True,
            dry_run=True
        )
        
        # Verify validation occurred but no files were processed
        assert progress.total_files == 3
        assert progress.processed == 3
        assert len(mock_backend.files) == 0  # No files actually ingested
    
    def test_batch_ingest_with_invalid_files(self, tmp_path, mock_backend):
        """Test batch ingestion handles invalid files gracefully."""
        from core.services.git_service import GitService
        from core.services.document_ingest_service import DocumentIngestService
        from core.services.batch_ingest_service import BatchIngestService
        
        # Create mix of valid and invalid files
        (tmp_path / "valid.md").write_text("# Valid Document")
        (tmp_path / "empty.md").write_text("")  # Invalid - empty
        (tmp_path / "invalid.pdf").write_text("Not supported")  # Invalid - format
        
        git_service = GitService()
        ingest_service = DocumentIngestService(mock_backend, git_service)
        batch_service = BatchIngestService(mock_backend, git_service, ingest_service)
        
        progress = batch_service.ingest_batch(
            directory=tmp_path,
            pattern="*.md,*.pdf",
            recursive=False
        )
        
        # Should process valid file and report errors for invalid ones
        assert progress.total_files == 3
        assert progress.succeeded == 1  # Only valid.md
        assert progress.failed == 2  # empty.md and invalid.pdf
        assert len(progress.errors) == 2


class TestTemporalQueries:
    """Test temporal query functionality."""
    
    def test_query_current_version(self, mock_backend):
        """Test querying current version of a file."""
        from core.services.query_service import QueryService
        
        # Set up mock data with multiple versions
        mock_backend.repositories['https://github.com/test/repo.git'] = {
            'id': 1,
            'repo_url': 'https://github.com/test/repo.git'
        }
        mock_backend.files = [
            {
                'id': 1,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'abc123',
                'valid_from': datetime(2025, 1, 1),
                'valid_until': datetime(2025, 1, 2)
            },
            {
                'id': 2,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'def456',
                'valid_from': datetime(2025, 1, 2),
                'valid_until': None  # Current version
            }
        ]
        
        query_service = QueryService(mock_backend)
        result = query_service.query_file('https://github.com/test/repo.git', 'docs/guide.md')
        
        assert result is not None
        assert result['id'] == 2
        assert result['commit_sha'] == 'def456'
        assert result['valid_until'] is None
    
    def test_query_at_specific_time(self, mock_backend):
        """Test querying file at specific timestamp."""
        from core.services.query_service import QueryService
        
        mock_backend.repositories['https://github.com/test/repo.git'] = {
            'id': 1,
            'repo_url': 'https://github.com/test/repo.git'
        }
        mock_backend.files = [
            {
                'id': 1,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'abc123',
                'valid_from': datetime(2025, 1, 1),
                'valid_until': datetime(2025, 1, 2)
            },
            {
                'id': 2,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'def456',
                'valid_from': datetime(2025, 1, 2),
                'valid_until': None
            }
        ]
        
        query_service = QueryService(mock_backend)
        
        # Query at time when first version was valid
        result = query_service.query_file(
            'https://github.com/test/repo.git',
            'docs/guide.md',
            timestamp=datetime(2025, 1, 1, 12, 0)
        )
        
        assert result is not None
        assert result['id'] == 1
        assert result['commit_sha'] == 'abc123'
    
    def test_query_at_specific_commit(self, mock_backend):
        """Test querying file at specific commit."""
        from core.services.query_service import QueryService
        
        mock_backend.repositories['https://github.com/test/repo.git'] = {
            'id': 1,
            'repo_url': 'https://github.com/test/repo.git'
        }
        mock_backend.files = [
            {
                'id': 1,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'abc123',
                'valid_from': datetime(2025, 1, 1),
                'valid_until': datetime(2025, 1, 2)
            },
            {
                'id': 2,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'def456',
                'valid_from': datetime(2025, 1, 2),
                'valid_until': None
            }
        ]
        
        query_service = QueryService(mock_backend)
        result = query_service.query_file(
            'https://github.com/test/repo.git',
            'docs/guide.md',
            commit_sha='abc123'
        )
        
        assert result is not None
        assert result['id'] == 1
        assert result['commit_sha'] == 'abc123'


class TestFileHistoryTracking:
    """Test file history tracking functionality."""
    
    def test_get_complete_file_history(self, mock_backend):
        """Test retrieving complete file history."""
        from core.services.query_service import QueryService
        
        mock_backend.repositories['https://github.com/test/repo.git'] = {
            'id': 1,
            'repo_url': 'https://github.com/test/repo.git'
        }
        mock_backend.files = [
            {
                'id': 1,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'commit1',
                'valid_from': datetime(2025, 1, 1),
                'valid_until': datetime(2025, 1, 2)
            },
            {
                'id': 2,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'commit2',
                'valid_from': datetime(2025, 1, 2),
                'valid_until': datetime(2025, 1, 3)
            },
            {
                'id': 3,
                'repo_id': 1,
                'file_path': 'docs/guide.md',
                'commit_sha': 'commit3',
                'valid_from': datetime(2025, 1, 3),
                'valid_until': None
            }
        ]
        
        query_service = QueryService(mock_backend)
        history = query_service.get_file_history('https://github.com/test/repo.git', 'docs/guide.md')
        
        assert len(history) == 3
        # Should be ordered by valid_from DESC
        assert history[0]['commit_sha'] == 'commit3'
        assert history[1]['commit_sha'] == 'commit2'
        assert history[2]['commit_sha'] == 'commit1'


class TestResumeCapability:
    """Test resume capability for interrupted batch operations."""
    
    def test_resume_after_interruption(self, tmp_path, mock_backend):
        """Test resuming batch ingestion after interruption."""
        from core.services.git_service import GitService
        from core.services.document_ingest_service import DocumentIngestService
        from core.services.batch_ingest_service import BatchIngestService
        import json
        
        # Create test files
        (tmp_path / "file1.md").write_text("# File 1")
        (tmp_path / "file2.md").write_text("# File 2")
        (tmp_path / "file3.md").write_text("# File 3")
        
        # Simulate previous run by creating progress file
        progress_file = tmp_path / ".batch_ingest_progress.json"
        completed_file = str((tmp_path / "file1.md").absolute())
        progress_data = {
            'version': '1.0',
            'completed_files': [completed_file],
            'last_updated': datetime.now().isoformat()
        }
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)
        
        # Create services
        git_service = GitService()
        ingest_service = DocumentIngestService(mock_backend, git_service)
        batch_service = BatchIngestService(mock_backend, git_service, ingest_service)
        
        # Resume batch ingestion
        progress = batch_service.ingest_batch(
            directory=tmp_path,
            pattern="*.md",
            recursive=False,
            resume=True
        )
        
        # Should skip file1 and process file2 and file3
        assert progress.total_files == 3
        assert progress.skipped == 1  # file1
        assert progress.succeeded == 2  # file2 and file3
        assert len(mock_backend.files) == 2  # Only file2 and file3 processed


@pytest.mark.integration
class TestCLIIntegration:
    """Test CLI command integration (requires actual CLI setup)."""
    
    def test_cli_commands_available(self):
        """Test that all CLI commands are registered."""
        from core.cli.rag import rag
        
        # Get all registered commands
        commands = list(rag.commands.keys())
        
        # Verify new commands are registered (Click converts underscores to hyphens)
        assert 'ingest-docs-batch' in commands
        assert 'query-file' in commands
        assert 'list-files' in commands
        assert 'file-history' in commands
        assert 'list-chunks' in commands
