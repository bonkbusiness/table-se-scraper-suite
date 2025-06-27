"""
scraper/cache.py

Persistent hash-based cache for Table.se product scraping.

This module provides a file-based cache system that supports change detection
via content hashes and enables efficient storage and retrieval of both raw HTML/content
and parsed product dictionaries. The cache helps avoid redundant scraping and enables
efficient incremental updates by detecting when content has changed.

Features:
    - Atomic, robust read/write operations with backup on corruption
    - MD5 hash content detection for cache validation
    - Supports storing by arbitrary key (SKU, URL, etc.)
    - Logging for all cache operations and error reporting
    - Backwards-compatible function-based API for legacy usage

Usage:
    from scraper.cache import Cache, hash_content, get_cached_product, update_cache

    cache = Cache()
    cache.set("SKU123", data, hash_content(html))
    cached = cache.get("SKU123", hash_of_html)

    # Legacy usage:
    update_cache("SKU123", data, hash_of_html)
    cached = get_cached_product("SKU123", hash_of_html)

Author: bonkbusiness
License: MIT
"""

import json
import os
import hashlib
import shutil
import tempfile
from typing import Optional, Any, Dict

try:
    from scraper.logging import get_logger
    logger = get_logger("cache")
except ImportError:
    import logging
    logger = logging.getLogger("cache")

DEFAULT_CACHE_FILE = "product_cache.json"

class Cache:
    """
    Hash-based, persistent cache for product scraping.
    Stores both raw HTML/content and parsed product dicts, supporting change detection.
    """

    def __init__(self, filename: str = DEFAULT_CACHE_FILE):
        """
        Initialize a cache instance with a specified filename.
        """
        self.filename = filename

    def load_cache(self) -> Dict[str, Any]:
        """
        Load the cache from disk. If corrupted, back up and start fresh.

        Returns:
            dict: The loaded cache, or empty if not found/corrupt.
        """
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                backup_file = self.filename + ".corrupt"
                shutil.copy2(self.filename, backup_file)
                logger.warning(
                    f"Cache file corrupted! Backup saved as {backup_file}. Starting with empty cache. ({e})"
                )
                return {}
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                return {}
        return {}

    def save_cache(self, cache: Dict[str, Any]):
        """
        Save the cache to disk atomically.

        Args:
            cache (dict): The cache to persist.
        """
        try:
            with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as tf:
                json.dump(cache, tf, ensure_ascii=False, indent=2)
                tempname = tf.name
            os.replace(tempname, self.filename)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    @staticmethod
    def hash_content(content: str) -> str:
        """
        Generate an MD5 hash of the content string for change detection.

        Args:
            content (str): String to hash.

        Returns:
            str: MD5 hex digest.
        """
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def get(self, key: str, content_hash: Optional[str] = None) -> Optional[Any]:
        """
        Return cached item if present and (if content_hash given) hash matches, else None.

        Args:
            key (str): Cache key (SKU, URL, etc).
            content_hash (str|None): If provided, checks value's hash.

        Returns:
            Any or None: Cached data or None if not found/mismatch.
        """
        cache = self.load_cache()
        item = cache.get(key)
        if item and (content_hash is None or item.get("hash") == content_hash):
            return item["data"]
        return None

    def exists(self, key: str, content_hash: Optional[str] = None) -> bool:
        """
        Check if a cache entry exists (and optionally matches hash).

        Args:
            key (str): Cache key.
            content_hash (str|None): Optionally, required hash.

        Returns:
            bool: Whether the cache entry exists and matches hash.
        """
        cache = self.load_cache()
        item = cache.get(key)
        if not item:
            return False
        if content_hash and item.get("hash") != content_hash:
            return False
        return True

    def set(self, key: str, data: Any, content_hash: str):
        """
        Store data in cache under key, with hash for change detection.

        Args:
            key (str): Cache key.
            data (Any): The data to store.
            content_hash (str): Hash of content for change detection.
        """
        if not key:
            logger.warning("Tried to cache an item with empty key!")
            return
        cache = self.load_cache()
        cache[key] = {"hash": content_hash, "data": data}
        logger.info(f"Updating cache for key: {key}")
        self.save_cache(cache)

    def invalidate(self, key: str):
        """
        Remove a key from the cache.

        Args:
            key (str): Cache key to remove.
        """
        cache = self.load_cache()
        if key in cache:
            del cache[key]
            logger.info(f"Invalidated cache for key: {key}")
            self.save_cache(cache)

# Backwards compatibility for legacy function-based usage
def load_cache() -> Dict[str, Any]:
    """
    Load the cache using default filename.
    """
    return Cache().load_cache()

def save_cache(cache: Dict[str, Any]):
    """
    Save the given cache using default filename.
    """
    return Cache().save_cache(cache)

def hash_content(content: str) -> str:
    """
    Generate MD5 hash using static method.
    """
    return Cache.hash_content(content)

def get_cached_product(sku: str, content_hash: Optional[str] = None) -> Optional[Any]:
    """
    Get cached product by SKU and optional content hash.
    """
    return Cache().get(sku, content_hash)

def update_cache(sku: str, data: Any, content_hash: str):
    """
    Update cache record for SKU.
    """
    return Cache().set(sku, data, content_hash)