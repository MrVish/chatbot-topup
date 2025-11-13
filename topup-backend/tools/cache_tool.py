"""
Cache Tool for Topup CXO Assistant.

This module implements an in-memory LRU (Least Recently Used) cache with TTL
(Time To Live) expiration. It stores query results including DataFrames,
Plotly specifications, and Insights to improve response times for repeated queries.

The cache uses a combination of:
- Timestamp-based TTL expiration (default 10 minutes)
- LRU eviction when cache size exceeds limit (default 100 entries)
- Thread-safe operations for concurrent access

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import json
import pickle
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

import pandas as pd


class CacheEntry:
    """
    Represents a single cache entry with value and expiration timestamp.
    
    Attributes:
        value: The cached value (can be dict, DataFrame, etc.)
        expires_at: Unix timestamp when this entry expires
        created_at: Unix timestamp when this entry was created
    """
    
    def __init__(self, value: Any, ttl: int):
        """
        Initialize a cache entry.
        
        Args:
            value: The value to cache
            ttl: Time to live in seconds
        """
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl
    
    def is_expired(self) -> bool:
        """
        Check if this cache entry has expired.
        
        Returns:
            bool: True if expired, False otherwise
        """
        return time.time() > self.expires_at


class InMemoryLRUCache:
    """
    In-memory LRU cache with TTL expiration.
    
    This cache implementation provides:
    - LRU eviction when max_size is exceeded
    - Automatic expiration of entries based on TTL
    - Thread-safe operations
    - Support for serializing pandas DataFrames
    
    Attributes:
        max_size: Maximum number of entries before LRU eviction
        default_ttl: Default TTL in seconds (600 = 10 minutes)
        _cache: OrderedDict storing cache entries (maintains insertion order)
        _lock: Threading lock for thread-safe operations
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 600):
        """
        Initialize the LRU cache.
        
        Args:
            max_size: Maximum number of entries (default: 100)
            default_ttl: Default TTL in seconds (default: 600 = 10 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value from the cache.
        
        This method:
        1. Checks if the key exists
        2. Validates the entry hasn't expired
        3. Moves the entry to the end (most recently used)
        4. Returns the value or None if missing/expired
        
        Args:
            key: Cache key (typically a hash of the query plan)
        
        Returns:
            Optional[Dict[str, Any]]: Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                return None
            
            # Move to end (mark as recently used)
            self._cache.move_to_end(key)
            
            # Deserialize DataFrames if present
            value = entry.value.copy()
            if 'df' in value and isinstance(value['df'], bytes):
                value['df'] = pickle.loads(value['df'])
            
            return value
    
    def set(self, key: str, value: Dict[str, Any], ex: Optional[int] = None) -> None:
        """
        Store a value in the cache.
        
        This method:
        1. Serializes pandas DataFrames for efficient storage
        2. Creates a cache entry with TTL
        3. Evicts least recently used entry if cache is full
        4. Stores the new entry
        
        Args:
            key: Cache key (typically a hash of the query plan)
            value: Value to cache (dict containing df, chart, insight)
            ex: TTL in seconds (uses default_ttl if not specified)
        """
        with self._lock:
            ttl = ex if ex is not None else self.default_ttl
            
            # Serialize DataFrames for storage
            serialized_value = value.copy()
            if 'df' in serialized_value and isinstance(serialized_value['df'], pd.DataFrame):
                serialized_value['df'] = pickle.dumps(serialized_value['df'])
            
            # Create cache entry
            entry = CacheEntry(serialized_value, ttl)
            
            # If key exists, remove it first (will be re-added at end)
            if key in self._cache:
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            
            # Evict LRU entry if cache is full
            if len(self._cache) > self.max_size:
                # Remove first item (least recently used)
                self._cache.popitem(last=False)
    
    def clear(self) -> None:
        """
        Clear all entries from the cache.
        
        This is useful for testing or manual cache invalidation.
        """
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """
        Get the current number of entries in the cache.
        
        Returns:
            int: Number of entries currently in cache
        """
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        This method can be called periodically to free up memory
        from expired entries that haven't been accessed.
        
        Returns:
            int: Number of expired entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)


# Global cache instance
_cache_instance: Optional[InMemoryLRUCache] = None


def get_cache() -> InMemoryLRUCache:
    """
    Get or create the global cache instance.
    
    This function implements a singleton pattern to ensure
    only one cache instance exists across the application.
    
    Returns:
        InMemoryLRUCache: The global cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = InMemoryLRUCache()
    return _cache_instance


def get(key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a value from the cache.
    
    Convenience function that uses the global cache instance.
    
    Args:
        key: Cache key (typically a hash of the query plan)
    
    Returns:
        Optional[Dict[str, Any]]: Cached value or None if not found/expired
    
    Example:
        >>> result = get("abc123...")
        >>> if result:
        >>>     df = result['df']
        >>>     chart = result['chart']
        >>>     insight = result['insight']
    """
    cache = get_cache()
    return cache.get(key)


def set(key: str, value: Dict[str, Any], ex: Optional[int] = None) -> None:
    """
    Store a value in the cache.
    
    Convenience function that uses the global cache instance.
    
    Args:
        key: Cache key (typically a hash of the query plan)
        value: Value to cache (dict containing df, chart, insight)
        ex: TTL in seconds (default: 600 = 10 minutes)
    
    Example:
        >>> set("abc123...", {
        >>>     'df': dataframe,
        >>>     'chart': plotly_spec,
        >>>     'insight': insight_obj
        >>> }, ex=600)
    """
    cache = get_cache()
    cache.set(key, value, ex)


def clear() -> None:
    """
    Clear all entries from the cache.
    
    Convenience function that uses the global cache instance.
    """
    cache = get_cache()
    cache.clear()


def cleanup_expired() -> int:
    """
    Remove all expired entries from the cache.
    
    Convenience function that uses the global cache instance.
    
    Returns:
        int: Number of expired entries removed
    """
    cache = get_cache()
    return cache.cleanup_expired()
