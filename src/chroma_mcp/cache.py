"""
Cache layer for passive short-term memory capabilities.
Provides caching without explicit commit to database.
"""
from typing import Dict, List, Optional, Any
import time
import json
from collections import OrderedDict
import hashlib


class CacheEntry:
    """Represents a cached entry with metadata."""
    
    def __init__(self, data: Any, ttl: int = 3600):
        self.data = data
        self.timestamp = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_access = time.time()
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.timestamp > self.ttl
    
    def access(self) -> Any:
        """Access the cached data and update access metadata."""
        self.access_count += 1
        self.last_access = time.time()
        return self.data


class MemoryCache:
    """
    Passive short-term memory cache layer for connected projects.
    Stores data temporarily without explicit commit to database.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._project_caches: Dict[str, OrderedDict] = {}
    
    def _generate_key(self, data: Any) -> str:
        """Generate a hash key for the data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _evict_if_needed(self, cache: OrderedDict):
        """Evict oldest entries if cache is full."""
        while len(cache) >= self.max_size:
            cache.popitem(last=False)
    
    def _cleanup_expired(self, cache: OrderedDict):
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del cache[key]
    
    def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[int] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Set data in cache.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default: 3600)
            project_id: Optional project ID for isolated caching
        
        Returns:
            Cache key
        """
        ttl = ttl or self.default_ttl
        cache = self._get_cache(project_id)
        
        self._cleanup_expired(cache)
        self._evict_if_needed(cache)
        
        entry = CacheEntry(data, ttl)
        cache[key] = entry
        cache.move_to_end(key)
        
        return key
    
    def get(
        self,
        key: str,
        project_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get data from cache.
        
        Args:
            key: Cache key
            project_id: Optional project ID for isolated caching
        
        Returns:
            Cached data or None if not found/expired
        """
        cache = self._get_cache(project_id)
        
        if key not in cache:
            return None
        
        entry = cache[key]
        if entry.is_expired():
            del cache[key]
            return None
        
        return entry.access()
    
    def _get_cache(self, project_id: Optional[str] = None) -> OrderedDict:
        """Get cache for a specific project or global cache."""
        if project_id:
            if project_id not in self._project_caches:
                self._project_caches[project_id] = OrderedDict()
            return self._project_caches[project_id]
        return self._cache
    
    def cache_query_result(
        self,
        query: str,
        result: Any,
        collection_name: str,
        project_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> str:
        """
        Cache a query result.
        
        Args:
            query: Query string
            result: Query result
            collection_name: Collection name
            project_id: Optional project ID
            ttl: Time to live in seconds
        
        Returns:
            Cache key
        """
        key = self._generate_key({
            "query": query,
            "collection": collection_name,
            "project": project_id
        })
        
        return self.set(key, result, ttl, project_id)
    
    def get_query_result(
        self,
        query: str,
        collection_name: str,
        project_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get cached query result.
        
        Args:
            query: Query string
            collection_name: Collection name
            project_id: Optional project ID
        
        Returns:
            Cached result or None
        """
        key = self._generate_key({
            "query": query,
            "collection": collection_name,
            "project": project_id
        })
        
        return self.get(key, project_id)
    
    def get_stats(self, project_id: Optional[str] = None) -> Dict:
        """Get cache statistics."""
        cache = self._get_cache(project_id)
        
        total_entries = len(cache)
        expired_count = sum(1 for entry in cache.values() if entry.is_expired())
        total_accesses = sum(entry.access_count for entry in cache.values())
        
        return {
            "total_entries": total_entries,
            "expired_count": expired_count,
            "active_entries": total_entries - expired_count,
            "total_accesses": total_accesses,
            "max_size": self.max_size,
            "default_ttl": self.default_ttl
        }
    
    def clear(self, project_id: Optional[str] = None):
        """Clear cache."""
        if project_id:
            if project_id in self._project_caches:
                self._project_caches[project_id].clear()
        else:
            self._cache.clear()
    
    def clear_all_projects(self):
        """Clear all project caches."""
        self._project_caches.clear()


# Global cache instance
_memory_cache = None

def get_memory_cache() -> MemoryCache:
    """Get or create the global memory cache."""
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache()
    return _memory_cache
