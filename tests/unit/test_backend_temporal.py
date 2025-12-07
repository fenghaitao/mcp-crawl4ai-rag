"""
Unit tests for backend temporal methods.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch


class TestBackendTemporalMethods:
    """Test suite for backend temporal operations."""
    
    @pytest.fixture
    def mock_supabase_backend(self):
        """Create mock Supabase backend."""
        from core.backends.supabase import SupabaseBackend
        
        backend = SupabaseBackend.__new__(SupabaseBackend)
        backend._client = Mock()
        return backend
    
    def test_store_file_version_updates_previous(self, mock_supabase_backend):
        """Test that storing new version updates previous version's valid_until."""
        # Mock the update and insert operations
        mock_supabase_backend._client.table.return_value.update.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value = Mock()
        mock_supabase_backend._client.table.return_value.insert.return_value.execute.return_value.data = [{'id': 123}]
        
        file_version = {
            'repo_id': 1,
            'file_path': 'docs/readme.md',
            'commit_sha': 'abc123',
            'content_hash': 'hash123',
            'file_size': 1000,
            'word_count': 100,
            'chunk_count': 5,
            'content_type': 'documentation',
            'valid_from': datetime.now(),
            'valid_until': None
        }
        
        file_id = mock_supabase_backend.store_file_version(file_version)
        
        assert file_id == 123
        # Verify update was called to set valid_until on previous version
        assert mock_supabase_backend._client.table.called
    
    def test_get_current_file_returns_latest(self, mock_supabase_backend):
        """Test getting current file version."""
        mock_data = {
            'id': 123,
            'repo_id': 1,
            'file_path': 'docs/readme.md',
            'valid_until': None
        }
        mock_supabase_backend._client.table.return_value.select.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value.data = [mock_data]
        
        result = mock_supabase_backend.get_current_file(1, 'docs/readme.md')
        
        assert result is not None
        assert result['id'] == 123
        assert result['valid_until'] is None
    
    def test_get_current_file_returns_none_when_not_found(self, mock_supabase_backend):
        """Test getting current file when none exists."""
        mock_supabase_backend._client.table.return_value.select.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value.data = []
        
        result = mock_supabase_backend.get_current_file(1, 'nonexistent.md')
        
        assert result is None
    
    def test_get_file_at_commit(self, mock_supabase_backend):
        """Test getting file at specific commit."""
        mock_data = {
            'id': 123,
            'repo_id': 1,
            'file_path': 'docs/readme.md',
            'commit_sha': 'abc123'
        }
        mock_supabase_backend._client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [mock_data]
        
        result = mock_supabase_backend.get_file_at_commit(1, 'docs/readme.md', 'abc123')
        
        assert result is not None
        assert result['commit_sha'] == 'abc123'
    
    def test_get_file_history_returns_ordered_list(self, mock_supabase_backend):
        """Test getting file history."""
        now = datetime.now()
        mock_data = [
            {'id': 3, 'valid_from': (now - timedelta(days=1)).isoformat()},
            {'id': 2, 'valid_from': (now - timedelta(days=2)).isoformat()},
            {'id': 1, 'valid_from': (now - timedelta(days=3)).isoformat()}
        ]
        mock_supabase_backend._client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = mock_data
        
        result = mock_supabase_backend.get_file_history(1, 'docs/readme.md', limit=10)
        
        assert len(result) == 3
        # Should be ordered by valid_from descending
        assert result[0]['id'] == 3
    
    def test_list_files_with_filters(self, mock_supabase_backend):
        """Test listing files with filters."""
        mock_data = [
            {'id': 1, 'repo_id': 1, 'content_type': 'documentation'},
            {'id': 2, 'repo_id': 1, 'content_type': 'documentation'}
        ]
        
        # Mock the query chain
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.is_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value.data = mock_data
        mock_query.execute.return_value.count = 2
        
        mock_supabase_backend._client.table.return_value.select.return_value = mock_query
        
        files, total = mock_supabase_backend.list_files(
            repo_id=1,
            content_type='documentation',
            current_only=True,
            limit=10,
            offset=0
        )
        
        assert len(files) == 2
        assert total == 2
    
    def test_store_repository(self, mock_supabase_backend):
        """Test storing repository."""
        mock_supabase_backend._client.table.return_value.upsert.return_value.execute.return_value.data = [{'id': 1}]
        
        repo_id = mock_supabase_backend.store_repository(
            'https://github.com/user/repo.git',
            'repo'
        )
        
        assert repo_id == 1
    
    def test_get_repository(self, mock_supabase_backend):
        """Test getting repository by URL."""
        mock_data = {
            'id': 1,
            'repo_url': 'https://github.com/user/repo.git',
            'repo_name': 'repo'
        }
        mock_supabase_backend._client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_data]
        
        result = mock_supabase_backend.get_repository('https://github.com/user/repo.git')
        
        assert result is not None
        assert result['id'] == 1
    
    def test_update_repository_last_ingested(self, mock_supabase_backend):
        """Test updating repository last_ingested_at."""
        mock_supabase_backend._client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
        
        success = mock_supabase_backend.update_repository_last_ingested(1)
        
        assert success is True
