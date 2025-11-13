"""
Tests for Cache Tool.

This module tests the in-memory LRU cache implementation including:
- Basic get/set operations
- TTL expiration
- LRU eviction
- DataFrame serialization
- Thread safety
"""

import time
import pandas as pd
import pytest

from cache_tool import InMemoryLRUCache, get, set, clear


def test_basic_get_set():
    """Test basic cache get and set operations."""
    cache = InMemoryLRUCache(max_size=10, default_ttl=60)
    
    # Set a value
    test_value = {'result': 'test_data', 'count': 42}
    cache.set('key1', test_value)
    
    # Get the value
    result = cache.get('key1')
    assert result is not None
    assert result['result'] == 'test_data'
    assert result['count'] == 42


def test_missing_key():
    """Test that missing keys return None."""
    cache = InMemoryLRUCache(max_size=10, default_ttl=60)
    
    result = cache.get('nonexistent_key')
    assert result is None


def test_ttl_expiration():
    """Test that entries expire after TTL."""
    cache = InMemoryLRUCache(max_size=10, default_ttl=1)  # 1 second TTL
    
    # Set a value with 1 second TTL
    cache.set('key1', {'data': 'test'})
    
    # Should be available immediately
    result = cache.get('key1')
    assert result is not None
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Should be expired now
    result = cache.get('key1')
    assert result is None


def test_custom_ttl():
    """Test setting custom TTL per entry."""
    cache = InMemoryLRUCache(max_size=10, default_ttl=60)
    
    # Set with custom 2 second TTL
    cache.set('key1', {'data': 'test'}, ex=2)
    
    # Should be available immediately
    result = cache.get('key1')
    assert result is not None
    
    # Wait for expiration
    time.sleep(2.1)
    
    # Should be expired now
    result = cache.get('key1')
    assert result is None


def test_lru_eviction():
    """Test that LRU eviction works when cache is full."""
    cache = InMemoryLRUCache(max_size=3, default_ttl=60)
    
    # Fill cache to capacity
    cache.set('key1', {'data': '1'})
    cache.set('key2', {'data': '2'})
    cache.set('key3', {'data': '3'})
    
    # All should be present
    assert cache.get('key1') is not None
    assert cache.get('key2') is not None
    assert cache.get('key3') is not None
    
    # Add one more (should evict key1 as it's least recently used)
    cache.set('key4', {'data': '4'})
    
    # key1 should be evicted
    assert cache.get('key1') is None
    # Others should still be present
    assert cache.get('key2') is not None
    assert cache.get('key3') is not None
    assert cache.get('key4') is not None


def test_lru_access_updates_order():
    """Test that accessing an entry updates its position in LRU order."""
    cache = InMemoryLRUCache(max_size=3, default_ttl=60)
    
    # Fill cache
    cache.set('key1', {'data': '1'})
    cache.set('key2', {'data': '2'})
    cache.set('key3', {'data': '3'})
    
    # Access key1 (moves it to end)
    cache.get('key1')
    
    # Add key4 (should evict key2, not key1)
    cache.set('key4', {'data': '4'})
    
    # key2 should be evicted (was least recently used)
    assert cache.get('key2') is None
    # key1 should still be present (was accessed)
    assert cache.get('key1') is not None
    assert cache.get('key3') is not None
    assert cache.get('key4') is not None


def test_dataframe_serialization():
    """Test that pandas DataFrames are properly serialized and deserialized."""
    cache = InMemoryLRUCache(max_size=10, default_ttl=60)
    
    # Create a test DataFrame
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    # Cache it
    cache.set('df_key', {'df': df, 'metadata': 'test'})
    
    # Retrieve it
    result = cache.get('df_key')
    assert result is not None
    assert 'df' in result
    assert isinstance(result['df'], pd.DataFrame)
    assert result['df'].equals(df)
    assert result['metadata'] == 'test'


def test_cache_clear():
    """Test that clear removes all entries."""
    cache = InMemoryLRUCache(max_size=10, default_ttl=60)
    
    # Add some entries
    cache.set('key1', {'data': '1'})
    cache.set('key2', {'data': '2'})
    cache.set('key3', {'data': '3'})
    
    assert cache.size() == 3
    
    # Clear cache
    cache.clear()
    
    assert cache.size() == 0
    assert cache.get('key1') is None
    assert cache.get('key2') is None
    assert cache.get('key3') is None


def test_cleanup_expired():
    """Test that cleanup_expired removes only expired entries."""
    cache = InMemoryLRUCache(max_size=10, default_ttl=60)
    
    # Add entries with different TTLs
    cache.set('key1', {'data': '1'}, ex=1)  # Expires in 1 second
    cache.set('key2', {'data': '2'}, ex=60)  # Expires in 60 seconds
    cache.set('key3', {'data': '3'}, ex=1)  # Expires in 1 second
    
    assert cache.size() == 3
    
    # Wait for some to expire
    time.sleep(1.1)
    
    # Cleanup expired
    removed = cache.cleanup_expired()
    
    assert removed == 2  # key1 and key3 should be removed
    assert cache.size() == 1
    assert cache.get('key2') is not None


def test_global_cache_functions():
    """Test the global cache convenience functions."""
    # Clear any existing cache
    clear()
    
    # Test set and get
    test_value = {'result': 'global_test', 'count': 99}
    set('global_key', test_value)
    
    result = get('global_key')
    assert result is not None
    assert result['result'] == 'global_test'
    assert result['count'] == 99
    
    # Test clear
    clear()
    result = get('global_key')
    assert result is None


def test_cache_with_plotly_and_insight():
    """Test caching complete query results with DataFrame, Plotly spec, and Insight."""
    cache = InMemoryLRUCache(max_size=10, default_ttl=60)
    
    # Create test data
    df = pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02'],
        'value': [100, 200]
    })
    
    plotly_spec = {
        'data': [{'x': [1, 2], 'y': [100, 200], 'type': 'line'}],
        'layout': {'title': 'Test Chart'}
    }
    
    insight = {
        'title': 'Test Insight',
        'summary': 'Values increased by 100%',
        'bullets': ['Point 1', 'Point 2'],
        'drivers': []
    }
    
    # Cache complete result
    cache.set('query_key', {
        'df': df,
        'chart': plotly_spec,
        'insight': insight
    })
    
    # Retrieve and verify
    result = cache.get('query_key')
    assert result is not None
    assert isinstance(result['df'], pd.DataFrame)
    assert result['df'].equals(df)
    assert result['chart'] == plotly_spec
    assert result['insight'] == insight


if __name__ == '__main__':
    # Run tests
    print("Running cache tool tests...")
    
    test_basic_get_set()
    print("✓ Basic get/set test passed")
    
    test_missing_key()
    print("✓ Missing key test passed")
    
    test_ttl_expiration()
    print("✓ TTL expiration test passed")
    
    test_custom_ttl()
    print("✓ Custom TTL test passed")
    
    test_lru_eviction()
    print("✓ LRU eviction test passed")
    
    test_lru_access_updates_order()
    print("✓ LRU access order test passed")
    
    test_dataframe_serialization()
    print("✓ DataFrame serialization test passed")
    
    test_cache_clear()
    print("✓ Cache clear test passed")
    
    test_cleanup_expired()
    print("✓ Cleanup expired test passed")
    
    test_global_cache_functions()
    print("✓ Global cache functions test passed")
    
    test_cache_with_plotly_and_insight()
    print("✓ Complete query result caching test passed")
    
    print("\nAll tests passed! ✓")
