"""
Property-based tests for hybrid search functionality.

These tests verify universal properties that should hold across all valid executions
of the hybrid search system.
"""

import os
import pytest
from hypothesis import given, strategies as st, settings
from core.backends.chroma import ChromaBackend


class TestHybridSearchProperties:
    """Property-based tests for hybrid search."""
    
    @given(env_value=st.one_of(
        st.just('true'),
        st.just('True'),
        st.just('TRUE'),
        st.just('1'),
        st.just('yes'),
        st.just('Yes'),
        st.just('YES'),
        st.just('false'),
        st.just('False'),
        st.just('FALSE'),
        st.just('0'),
        st.just('no'),
        st.just('No'),
        st.just('NO'),
        st.just(''),
        st.text(min_size=1, max_size=20).filter(
            lambda x: '\x00' not in x and x.lower() not in ('true', '1', 'yes', 'false', '0', 'no', '')
        )
    ))
    @settings(max_examples=100, deadline=None)
    def test_property_1_environment_variable_parsing_correctness(self, env_value):
        """
        **Feature: hybrid-search, Property 1: Environment variable parsing correctness**
        **Validates: Requirements 1.1, 1.2, 1.3**
        
        For any environment variable value, the system should correctly identify
        whether hybrid search should be enabled (truthy values: true, 1, yes) or
        disabled (all other values or absence).
        """
        # Set the environment variable
        if env_value == '':
            # Test with unset variable
            os.environ.pop('USE_HYBRID_SEARCH', None)
        else:
            os.environ['USE_HYBRID_SEARCH'] = env_value
        
        try:
            # Create backend instance
            backend = ChromaBackend()
            
            # Check if hybrid search is enabled
            is_enabled = backend._is_hybrid_search_enabled()
            
            # Verify correctness
            expected_enabled = env_value.lower() in ('true', '1', 'yes')
            
            assert is_enabled == expected_enabled, (
                f"Environment variable '{env_value}' should result in "
                f"hybrid_search_enabled={expected_enabled}, but got {is_enabled}"
            )
            
        finally:
            # Clean up environment
            os.environ.pop('USE_HYBRID_SEARCH', None)
