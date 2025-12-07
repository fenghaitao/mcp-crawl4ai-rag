"""
Unit tests for enhanced DocumentIngestService with repository support.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


class TestDocumentIngestServiceWithGit:
    """Test suite for DocumentIngestService with git integration."""
    
    @pytest.fixture
    def mock_backend(self):
        """Create mock backend."""
        backend = Mock()
        backend.get_repository.return_value = None
        backend.store_repository.return_value = 1
        backend.store_file_version.return_value = 123
        backend.update_repository_last_ingested.return_value = True
        return backend
    
    @pytest.fixture
    def mock_git_service(self):
        """Create mock git service."""
        from core.services.git_service import GitInfo
        
        git_service = Mock()
        git_info = GitInfo(
            repo_root=Path("/path/to/repo"),
            repo_url="https://github.com/user/repo.git",
            commit_sha="abc123",
            commit_timestamp=datetime.now()
        )
        git_service.detect_repository.return_value = git_info
        return git_service
    
    def test_ingest_with_git_repository(self, mock_backend, mock_git_service):
        """Test ingesting file from git repository."""
        from core.services.document_ingest_service import DocumentIngestService
        
        service = DocumentIngestService(mock_backend, mock_git_service)
        
        # Mock file operations
        with patch.object(service, '_calculate_file_hash', return_value='hash123'):
            with patch.object(service, '_get_file_stats', return_value={'size': 1000, 'modified_time': 123456}):
                with patch.object(service, '_check_existing_file', return_value=None):
                    with patch.object(service, '_get_chunker'):
                        with patch.object(service, '_store_chunks', return_value={'chunks': 5, 'words': 100}):
                            result = service.ingest_document('/path/to/repo/file.md')
        
        # Verify git detection was called
        assert mock_git_service.detect_repository.called
        
        # Verify repository was stored
        assert mock_backend.store_repository.called or mock_backend.get_repository.called
        
        # Verify file version was stored
        assert mock_backend.store_file_version.called
    
    def test_ingest_without_git_repository(self, mock_backend):
        """Test ingesting file outside git repository."""
        from core.services.document_ingest_service import DocumentIngestService
        
        git_service = Mock()
        git_service.detect_repository.return_value = None
        
        service = DocumentIngestService(mock_backend, git_service)
        mock_backend.store_file_record.return_value = 123
        
        # Mock file operations
        with patch.object(service, '_calculate_file_hash', return_value='hash123'):
            with patch.object(service, '_get_file_stats', return_value={'size': 1000, 'modified_time': 123456}):
                with patch.object(service, '_check_existing_file', return_value=None):
                    with patch.object(service, '_get_chunker'):
                        with patch.object(service, '_store_chunks', return_value={'chunks': 5, 'words': 100}):
                            result = service.ingest_document('/path/to/file.md')
        
        # Verify fallback to legacy method
        assert mock_backend.store_file_record.called
        assert not mock_backend.store_file_version.called
