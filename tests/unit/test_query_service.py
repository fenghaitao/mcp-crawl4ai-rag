"""
Unit tests for QueryService.

Tests file queries, temporal queries, file listing, file history, and chunk operations.
"""

import pytest
from datetime import datetime
from core.services.query_service import QueryService


class MockBackend:
    """Mock backend for testing QueryService."""
    
    def __init__(self):
        self.repositories = {
            'https://github.com/test/repo.git': {'id': 1, 'repo_url': 'https://github.com/test/repo.git'}
        }
        self.files = []
        self.chunks = []
    
    def get_repository(self, repo_url):
        return self.repositories.get(repo_url)
    
    def get_current_file(self, repo_id, file_path):
        for f in self.files:
            if f['repo_id'] == repo_id and f['file_path'] == file_path and f.get('valid_until') is None:
                return f
        return None
    
    def get_file_at_time(self, repo_id, file_path, timestamp):
        for f in self.files:
            if (f['repo_id'] == repo_id and f['file_path'] == file_path and
                f['valid_from'] <= timestamp and
                (f.get('valid_until') is None or f['valid_until'] > timestamp)):
                return f
        return None
    
    def get_file_at_commit(self, repo_id, file_path, commit_sha):
        for f in self.files:
            if f['repo_id'] == repo_id and f['file_path'] == file_path and f['commit_sha'] == commit_sha:
                return f
        return None
    
    def get_file_history(self, repo_id, file_path, limit):
        history = [f for f in self.files if f['repo_id'] == repo_id and f['file_path'] == file_path]
        history.sort(key=lambda x: x['valid_from'], reverse=True)
        return history[:limit]
    
    def list_files(self, repo_id=None, content_type=None, current_only=True, limit=100, offset=0):
        filtered = self.files
        
        if repo_id is not None:
            filtered = [f for f in filtered if f['repo_id'] == repo_id]
        
        if content_type:
            filtered = [f for f in filtered if f.get('content_type') == content_type]
        
        if current_only:
            filtered = [f for f in filtered if f.get('valid_until') is None]
        
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        return (paginated, total)
    
    def get_chunks_by_file_id(self, file_id):
        chunks = [c for c in self.chunks if c['file_id'] == file_id]
        chunks.sort(key=lambda x: x['chunk_number'])
        return chunks
    
    def search_chunks(self, content_type=None, has_code=None, metadata_filter=None, limit=100):
        filtered = self.chunks
        
        if content_type:
            filtered = [c for c in filtered if c.get('content_type') == content_type]
        
        if has_code is not None:
            filtered = [c for c in filtered if c.get('has_code') == has_code]
        
        if metadata_filter:
            for key, value in metadata_filter.items():
                filtered = [c for c in filtered if c.get('metadata', {}).get(key) == value]
        
        return filtered[:limit]


class TestQueryFile:
    """Test file query methods."""
    
    def test_query_current_file(self):
        """Test querying current file version."""
        backend = MockBackend()
        backend.files = [
            {
                'id': 1,
                'repo_id': 1,
                'file_path': 'docs/readme.md',
                'commit_sha': 'abc123',
                'valid_from': datetime(2025, 1, 1),
                'valid_until': None
            }
        ]
        
        service = QueryService(backend)
        result = service.query_file('https://github.com/test/repo.git', 'docs/readme.md')
        
        assert result is not None
        assert result['id'] == 1
        assert result['commit_sha'] == 'abc123'
    
    def test_query_file_at_commit(self):
        """Test querying file at specific commit."""
        backend = MockBackend()
        backend.files = [
            {
                'id': 1,
                'repo_id': 1,
                'file_path': 'docs/readme.md',
                'commit_sha': 'abc123',
                'valid_from': datetime(2025, 1, 1),
                'valid_until': datetime(2025, 1, 2)
            },
            {
                'id': 2,
                'repo_id': 1,
                'file_path': 'docs/readme.md',
                'commit_sha': 'def456',
                'valid_from': datetime(2025, 1, 2),
                'valid_until': None
            }
        ]
        
        service = QueryService(backend)
        result = service.query_file(
            'https://github.com/test/repo.git',
            'docs/readme.md',
            commit_sha='abc123'
        )
        
        assert result is not None
        assert result['id'] == 1
        assert result['commit_sha'] == 'abc123'
    
    def test_query_file_at_timestamp(self):
        """Test querying file at specific timestamp."""
        backend = MockBackend()
        backend.files = [
            {
                'id': 1,
                'repo_id': 1,
                'file_path': 'docs/readme.md',
                'commit_sha': 'abc123',
                'valid_from': datetime(2025, 1, 1),
                'valid_until': datetime(2025, 1, 2)
            },
            {
                'id': 2,
                'repo_id': 1,
                'file_path': 'docs/readme.md',
                'commit_sha': 'def456',
                'valid_from': datetime(2025, 1, 2),
                'valid_until': None
            }
        ]
        
        service = QueryService(backend)
        result = service.query_file(
            'https://github.com/test/repo.git',
            'docs/readme.md',
            timestamp=datetime(2025, 1, 1, 12, 0)
        )
        
        assert result is not None
        assert result['id'] == 1
        assert result['commit_sha'] == 'abc123'
    
    def test_query_file_nonexistent_repo(self):
        """Test querying file from nonexistent repository."""
        backend = MockBackend()
        service = QueryService(backend)
        
        result = service.query_file('https://github.com/nonexistent/repo.git', 'docs/readme.md')
        
        assert result is None


class TestListFiles:
    """Test file listing methods."""
    
    def test_list_all_files(self):
        """Test listing all files."""
        backend = MockBackend()
        backend.files = [
            {'id': 1, 'repo_id': 1, 'file_path': 'file1.md', 'valid_until': None},
            {'id': 2, 'repo_id': 1, 'file_path': 'file2.md', 'valid_until': None},
        ]
        
        service = QueryService(backend)
        files, total = service.list_files()
        
        assert len(files) == 2
        assert total == 2
    
    def test_list_files_by_repo(self):
        """Test listing files filtered by repository."""
        backend = MockBackend()
        backend.repositories['https://github.com/test/repo2.git'] = {'id': 2, 'repo_url': 'https://github.com/test/repo2.git'}
        backend.files = [
            {'id': 1, 'repo_id': 1, 'file_path': 'file1.md', 'valid_until': None},
            {'id': 2, 'repo_id': 2, 'file_path': 'file2.md', 'valid_until': None},
        ]
        
        service = QueryService(backend)
        files, total = service.list_files(repo_url='https://github.com/test/repo.git')
        
        assert len(files) == 1
        assert files[0]['repo_id'] == 1
    
    def test_list_files_by_content_type(self):
        """Test listing files filtered by content type."""
        backend = MockBackend()
        backend.files = [
            {'id': 1, 'repo_id': 1, 'file_path': 'file1.md', 'content_type': 'documentation', 'valid_until': None},
            {'id': 2, 'repo_id': 1, 'file_path': 'file2.py', 'content_type': 'python_test', 'valid_until': None},
        ]
        
        service = QueryService(backend)
        files, total = service.list_files(content_type='documentation')
        
        assert len(files) == 1
        assert files[0]['content_type'] == 'documentation'
    
    def test_list_files_with_pagination(self):
        """Test listing files with pagination."""
        backend = MockBackend()
        backend.files = [
            {'id': i, 'repo_id': 1, 'file_path': f'file{i}.md', 'valid_until': None}
            for i in range(1, 11)
        ]
        
        service = QueryService(backend)
        files, total = service.list_files(limit=5, offset=0)
        
        assert len(files) == 5
        assert total == 10
        assert files[0]['id'] == 1
        
        files, total = service.list_files(limit=5, offset=5)
        assert len(files) == 5
        assert files[0]['id'] == 6
    
    def test_list_files_nonexistent_repo(self):
        """Test listing files from nonexistent repository."""
        backend = MockBackend()
        service = QueryService(backend)
        
        files, total = service.list_files(repo_url='https://github.com/nonexistent/repo.git')
        
        assert len(files) == 0
        assert total == 0


class TestFileHistory:
    """Test file history methods."""
    
    def test_get_file_history(self):
        """Test getting file version history."""
        backend = MockBackend()
        backend.files = [
            {
                'id': 1,
                'repo_id': 1,
                'file_path': 'docs/readme.md',
                'commit_sha': 'abc123',
                'valid_from': datetime(2025, 1, 1),
                'valid_until': datetime(2025, 1, 2)
            },
            {
                'id': 2,
                'repo_id': 1,
                'file_path': 'docs/readme.md',
                'commit_sha': 'def456',
                'valid_from': datetime(2025, 1, 2),
                'valid_until': datetime(2025, 1, 3)
            },
            {
                'id': 3,
                'repo_id': 1,
                'file_path': 'docs/readme.md',
                'commit_sha': 'ghi789',
                'valid_from': datetime(2025, 1, 3),
                'valid_until': None
            }
        ]
        
        service = QueryService(backend)
        history = service.get_file_history('https://github.com/test/repo.git', 'docs/readme.md')
        
        assert len(history) == 3
        # Should be ordered by valid_from DESC
        assert history[0]['commit_sha'] == 'ghi789'
        assert history[1]['commit_sha'] == 'def456'
        assert history[2]['commit_sha'] == 'abc123'
    
    def test_get_file_history_with_limit(self):
        """Test getting file history with limit."""
        backend = MockBackend()
        backend.files = [
            {'id': i, 'repo_id': 1, 'file_path': 'docs/readme.md', 'commit_sha': f'commit{i}',
             'valid_from': datetime(2025, 1, i), 'valid_until': None if i == 5 else datetime(2025, 1, i+1)}
            for i in range(1, 6)
        ]
        
        service = QueryService(backend)
        history = service.get_file_history('https://github.com/test/repo.git', 'docs/readme.md', limit=2)
        
        assert len(history) == 2
    
    def test_get_file_history_nonexistent_repo(self):
        """Test getting history from nonexistent repository."""
        backend = MockBackend()
        service = QueryService(backend)
        
        history = service.get_file_history('https://github.com/nonexistent/repo.git', 'docs/readme.md')
        
        assert len(history) == 0


class TestChunkOperations:
    """Test chunk retrieval and search methods."""
    
    def test_get_file_chunks(self):
        """Test getting chunks for a file."""
        backend = MockBackend()
        backend.chunks = [
            {'id': 1, 'file_id': 1, 'chunk_number': 0, 'content': 'Chunk 0'},
            {'id': 2, 'file_id': 1, 'chunk_number': 1, 'content': 'Chunk 1'},
            {'id': 3, 'file_id': 2, 'chunk_number': 0, 'content': 'Other file'},
        ]
        
        service = QueryService(backend)
        chunks = service.get_file_chunks(1)
        
        assert len(chunks) == 2
        assert chunks[0]['chunk_number'] == 0
        assert chunks[1]['chunk_number'] == 1
    
    def test_get_file_chunks_empty(self):
        """Test getting chunks for file with no chunks."""
        backend = MockBackend()
        service = QueryService(backend)
        
        chunks = service.get_file_chunks(999)
        
        assert len(chunks) == 0
    
    def test_search_chunks_by_content_type(self):
        """Test searching chunks by content type."""
        backend = MockBackend()
        backend.chunks = [
            {'id': 1, 'file_id': 1, 'content_type': 'documentation', 'content': 'Doc chunk'},
            {'id': 2, 'file_id': 2, 'content_type': 'code_dml', 'content': 'Code chunk'},
        ]
        
        service = QueryService(backend)
        chunks = service.search_chunks(content_type='documentation')
        
        assert len(chunks) == 1
        assert chunks[0]['content_type'] == 'documentation'
    
    def test_search_chunks_by_has_code(self):
        """Test searching chunks by has_code flag."""
        backend = MockBackend()
        backend.chunks = [
            {'id': 1, 'file_id': 1, 'has_code': True, 'content': 'Chunk with code'},
            {'id': 2, 'file_id': 2, 'has_code': False, 'content': 'Chunk without code'},
        ]
        
        service = QueryService(backend)
        chunks = service.search_chunks(has_code=True)
        
        assert len(chunks) == 1
        assert chunks[0]['has_code'] is True
    
    def test_search_chunks_by_metadata(self):
        """Test searching chunks by metadata filter."""
        backend = MockBackend()
        backend.chunks = [
            {'id': 1, 'file_id': 1, 'metadata': {'section': 'intro'}, 'content': 'Intro chunk'},
            {'id': 2, 'file_id': 2, 'metadata': {'section': 'conclusion'}, 'content': 'Conclusion chunk'},
        ]
        
        service = QueryService(backend)
        chunks = service.search_chunks(metadata_filter={'section': 'intro'})
        
        assert len(chunks) == 1
        assert chunks[0]['metadata']['section'] == 'intro'
    
    def test_search_chunks_multiple_filters(self):
        """Test searching chunks with multiple filters (AND logic)."""
        backend = MockBackend()
        backend.chunks = [
            {'id': 1, 'file_id': 1, 'content_type': 'documentation', 'has_code': True, 'content': 'Doc with code'},
            {'id': 2, 'file_id': 2, 'content_type': 'documentation', 'has_code': False, 'content': 'Doc without code'},
            {'id': 3, 'file_id': 3, 'content_type': 'code_dml', 'has_code': True, 'content': 'Code chunk'},
        ]
        
        service = QueryService(backend)
        chunks = service.search_chunks(content_type='documentation', has_code=True)
        
        assert len(chunks) == 1
        assert chunks[0]['id'] == 1
