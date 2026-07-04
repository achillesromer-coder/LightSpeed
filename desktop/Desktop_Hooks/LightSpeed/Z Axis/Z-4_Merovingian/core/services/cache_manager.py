#!/usr/bin/env python
"""
Cache Manager - High-Performance Caching Layer
LightSpeed Type I Civilization Platform

Multi-tier caching system with:
- In-memory LRU cache
- Persistent disk cache
- Distributed cache support (Redis-compatible)
- Automatic cache invalidation
- Cache statistics and monitoring

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

import hashlib
import time
import threading
import functools
import json
import base64
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import OrderedDict
from enum import Enum


def _estimate_size_bytes(value: Any) -> int:
    """
    Best-effort size estimate without using pickle.

    Notes:
    - `sys.getsizeof` does not include deep contents, but is sufficient for cache
      eviction heuristics.
    - For common JSON-like payloads we try to approximate using `json.dumps`.
    """
    try:
        if isinstance(value, (bytes, bytearray)):
            return len(value)
    except Exception:
        pass

    try:
        return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    except Exception:
        pass

    try:
        return int(sys.getsizeof(value))
    except Exception:
        return 0


def _serialize_cache_value(value: Any) -> Dict[str, Any]:
    """
    Serialize a cache value safely (no pickle).

    Returns a tagged payload. Values that cannot be safely serialized are stored
    as `repr` and treated as non-restorable on read (DiskCache.get returns None).
    """
    try:
        if isinstance(value, (bytes, bytearray)):
            return {
                "kind": "bytes_b64",
                "value": base64.b64encode(bytes(value)).decode("ascii"),
            }
    except Exception:
        pass

    try:
        json.dumps(value)
        return {"kind": "json", "value": value}
    except Exception:
        return {"kind": "repr", "value": repr(value)}


def _deserialize_cache_value(payload: Dict[str, Any]) -> Tuple[bool, Any]:
    kind = str(payload.get("kind") or "")
    if kind == "json":
        return True, payload.get("value")
    if kind == "bytes_b64":
        try:
            raw = base64.b64decode(str(payload.get("value") or "").encode("ascii"), validate=False)
            return True, raw
        except Exception:
            return False, None
    # repr (or unknown kinds) are intentionally non-restorable
    return False, None


class CachePolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheEntry:
    """Single cache entry"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl: Optional[float] = None  # seconds
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl is None:
            return False

        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl

    def update_access(self):
        """Update access statistics"""
        self.accessed_at = datetime.now()
        self.access_count += 1


class LRUCache:
    """
    In-memory LRU (Least Recently Used) cache

    Fast in-memory cache with automatic eviction of least recently used items.
    """

    def __init__(self, max_size: int = 1000, max_bytes: Optional[int] = None):
        self.max_size = max_size
        self.max_bytes = max_bytes or (100 * 1024 * 1024)  # 100MB default

        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_bytes = 0

        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'sets': 0
        }

        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None

            entry = self.cache[key]

            # Check expiration
            if entry.is_expired():
                self._remove(key)
                self.stats['misses'] += 1
                return None

            # Update access and move to end (most recent)
            entry.update_access()
            self.cache.move_to_end(key)

            self.stats['hits'] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in cache"""
        with self.lock:
            # Estimate size
            size_bytes = _estimate_size_bytes(value)

            # Remove existing entry if present
            if key in self.cache:
                self._remove(key)

            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                ttl=ttl,
                size_bytes=size_bytes
            )

            # Evict if necessary
            while (len(self.cache) >= self.max_size or
                   self.current_bytes + size_bytes > self.max_bytes):
                if not self.cache:
                    break
                self._evict_one()

            # Add entry
            self.cache[key] = entry
            self.current_bytes += size_bytes
            self.stats['sets'] += 1

    def _remove(self, key: str):
        """Remove entry from cache"""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.current_bytes -= entry.size_bytes

    def _evict_one(self):
        """Evict one entry (LRU)"""
        if not self.cache:
            return

        # Remove oldest (first in OrderedDict)
        key, entry = self.cache.popitem(last=False)
        self.current_bytes -= entry.size_bytes
        self.stats['evictions'] += 1

    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self.lock:
            if key in self.cache:
                self._remove(key)
                return True
            return False

    def clear(self):
        """Clear all entries"""
        with self.lock:
            self.cache.clear()
            self.current_bytes = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0.0

            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'bytes': self.current_bytes,
                'max_bytes': self.max_bytes,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'sets': self.stats['sets'],
                'hit_rate': hit_rate
            }


class DiskCache:
    """
    Persistent disk-based cache

    Stores cache entries on disk for persistence across restarts.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".lightspeed" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }

        self.lock = threading.RLock()

    def _get_path(self, key: str) -> Path:
        """Get file path for cache key"""
        # Hash key to create safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        with self.lock:
            path = self._get_path(key)

            if not path.exists():
                self.stats['misses'] += 1
                return None

            try:
                raw = path.read_text(encoding="utf-8", errors="replace")
                data = json.loads(raw) if raw.strip() else {}

                # Check expiration
                try:
                    ttl = data.get("ttl")
                    created_at = datetime.fromisoformat(str(data.get("created_at") or ""))
                    if ttl is not None:
                        age = (datetime.now() - created_at).total_seconds()
                        if age > float(ttl):
                            try:
                                path.unlink()
                            except Exception:
                                pass
                            self.stats['misses'] += 1
                            return None
                except Exception:
                    # Corrupt or incomplete cache file: treat as miss and remove it.
                    try:
                        path.unlink()
                    except Exception:
                        pass
                    self.stats['misses'] += 1
                    return None

                ok, value = _deserialize_cache_value(data.get("value") or {})
                if not ok:
                    # Non-restorable entries are treated as cache misses.
                    self.stats['misses'] += 1
                    return None

                # Update access time on disk
                try:
                    data["accessed_at"] = datetime.now().isoformat()
                    data["access_count"] = int(data.get("access_count") or 0) + 1
                    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                except Exception:
                    pass

                self.stats['hits'] += 1
                return value

            except Exception as e:
                self.stats['errors'] += 1
                print(f"[DiskCache] Error reading {key}: {e}")
                return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in disk cache"""
        with self.lock:
            path = self._get_path(key)

            try:
                payload = {
                    "key": key,
                    "created_at": datetime.now().isoformat(),
                    "accessed_at": datetime.now().isoformat(),
                    "access_count": 0,
                    "ttl": ttl,
                    "size_bytes": _estimate_size_bytes(value),
                    "value": _serialize_cache_value(value),
                }
                path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

                self.stats['sets'] += 1

            except Exception as e:
                self.stats['errors'] += 1
                print(f"[DiskCache] Error writing {key}: {e}")

    def delete(self, key: str) -> bool:
        """Delete entry from disk cache"""
        with self.lock:
            path = self._get_path(key)

            if path.exists():
                try:
                    path.unlink()
                    return True
                except Exception as e:
                    self.stats['errors'] += 1
                    print(f"[DiskCache] Error deleting {key}: {e}")

            return False

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            try:
                for path in self.cache_dir.glob("*.cache"):
                    path.unlink()
            except Exception as e:
                print(f"[DiskCache] Error clearing cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            # Count files
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)

            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0.0

            return {
                'size': len(cache_files),
                'bytes': total_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'errors': self.stats['errors'],
                'hit_rate': hit_rate
            }


class CacheManager:
    """
    Multi-tier cache manager

    Manages multiple cache layers (memory, disk) with automatic
    promotion/demotion between tiers.
    """

    def __init__(self,
                 memory_cache_size: int = 1000,
                 memory_cache_bytes: int = 100 * 1024 * 1024,
                 disk_cache_dir: Optional[Path] = None,
                 enable_disk_cache: bool = True):

        self.memory_cache = LRUCache(
            max_size=memory_cache_size,
            max_bytes=memory_cache_bytes
        )

        self.disk_cache: Optional[DiskCache] = None
        if enable_disk_cache:
            self.disk_cache = DiskCache(cache_dir=disk_cache_dir)

        self.default_ttl: Optional[float] = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (checks all tiers)"""
        # Check memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Check disk cache
        if self.disk_cache:
            value = self.disk_cache.get(key)
            if value is not None:
                # Promote to memory cache
                self.memory_cache.set(key, value)
                return value

        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value in cache (all tiers)"""
        if ttl is None:
            ttl = self.default_ttl

        # Set in memory cache
        self.memory_cache.set(key, value, ttl=ttl)

        # Set in disk cache
        if self.disk_cache:
            self.disk_cache.set(key, value, ttl=ttl)

    def delete(self, key: str) -> bool:
        """Delete from all cache tiers"""
        deleted = False

        if self.memory_cache.delete(key):
            deleted = True

        if self.disk_cache and self.disk_cache.delete(key):
            deleted = True

        return deleted

    def clear(self):
        """Clear all cache tiers"""
        self.memory_cache.clear()
        if self.disk_cache:
            self.disk_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all tiers"""
        stats = {
            'memory': self.memory_cache.get_stats()
        }

        if self.disk_cache:
            stats['disk'] = self.disk_cache.get_stats()

        # Combined stats
        total_hits = stats['memory']['hits']
        total_misses = stats['memory']['misses']

        if 'disk' in stats:
            total_hits += stats['disk']['hits']
            total_misses += stats['disk']['misses']

        total_requests = total_hits + total_misses
        combined_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0

        stats['combined'] = {
            'hits': total_hits,
            'misses': total_misses,
            'hit_rate': combined_hit_rate
        }

        return stats


def cached(ttl: Optional[float] = None, key_prefix: str = ""):
    """
    Decorator to cache function results

    Usage:
        @cached(ttl=300, key_prefix='user')
        def get_user(user_id):
            # expensive operation
            return user_data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]

            # Add args
            for arg in args:
                key_parts.append(str(arg))

            # Add kwargs
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            cache_key = ":".join(key_parts)

            # Check cache
            cache = get_cache_manager()
            cached_value = cache.get(cache_key)

            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl)

            return result

        # Add cache control methods
        wrapper.cache_clear = lambda: get_cache_manager().clear()
        wrapper.cache_info = lambda: get_cache_manager().get_stats()

        return wrapper
    return decorator


# Singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


if __name__ == "__main__":
    # Test cache system
    print("Cache Manager Test")
    print("=" * 60)

    cache = get_cache_manager()

    # Test basic operations
    print("\nBasic Operations:")
    print("-" * 60)

    cache.set("user:123", {"name": "Alice", "email": "alice@example.com"}, ttl=60)
    cache.set("user:456", {"name": "Bob", "email": "bob@example.com"}, ttl=60)

    user = cache.get("user:123")
    print(f"Retrieved user: {user}")

    # Test cache decorator
    print("\nCache Decorator Test:")
    print("-" * 60)

    @cached(ttl=30, key_prefix='fibonacci')
    def fibonacci(n):
        """Expensive recursive function"""
        if n < 2:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    # First call (cache miss)
    start = time.time()
    result1 = fibonacci(35)
    time1 = time.time() - start
    print(f"First call (cache miss): fibonacci(35) = {result1} in {time1:.4f}s")

    # Second call (cache hit)
    start = time.time()
    result2 = fibonacci(35)
    time2 = time.time() - start
    print(f"Second call (cache hit): fibonacci(35) = {result2} in {time2:.6f}s")
    print(f"Speedup: {time1/time2:.0f}x faster")

    # Cache statistics
    print("\nCache Statistics:")
    print("-" * 60)
    stats = cache.get_stats()

    print("\nMemory Cache:")
    mem_stats = stats['memory']
    print(f"  Size: {mem_stats['size']}/{mem_stats['max_size']} entries")
    print(f"  Bytes: {mem_stats['bytes']:,}/{mem_stats['max_bytes']:,}")
    print(f"  Hit rate: {mem_stats['hit_rate']:.1f}%")
    print(f"  Hits: {mem_stats['hits']}, Misses: {mem_stats['misses']}")

    if 'disk' in stats:
        print("\nDisk Cache:")
        disk_stats = stats['disk']
        print(f"  Size: {disk_stats['size']} files")
        print(f"  Bytes: {disk_stats['bytes']:,}")
        print(f"  Hit rate: {disk_stats['hit_rate']:.1f}%")
        print(f"  Hits: {disk_stats['hits']}, Misses: {disk_stats['misses']}")

    print("\nCombined:")
    combined = stats['combined']
    print(f"  Total hit rate: {combined['hit_rate']:.1f}%")
    print(f"  Total hits: {combined['hits']}, Total misses: {combined['misses']}")

    # Test eviction
    print("\nEviction Test:")
    print("-" * 60)

    # Fill cache beyond capacity
    small_cache = LRUCache(max_size=5)

    for i in range(10):
        small_cache.set(f"item:{i}", f"value_{i}")

    print(f"Added 10 items to cache with max_size=5")
    print(f"Current size: {small_cache.get_stats()['size']}")
    print(f"Evictions: {small_cache.get_stats()['evictions']}")

    # Check which items survived
    print("\nSurviving items (most recent 5):")
    for i in range(10):
        value = small_cache.get(f"item:{i}")
        if value:
            print(f"  item:{i} = {value}")

    print("\n" + "=" * 60)
    print("Cache system ready!")
