import json
import os
import hashlib

CACHE_FILE = "product_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def hash_content(content):
    """Generate an MD5 hash of the content string for change detection."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def get_cached_product(sku, content_hash=None):
    """
    Return cached product dict if present and (if content_hash given) hash matches,
    else None. SKU/artikelnummer is used as key.
    """
    cache = load_cache()
    product = cache.get(sku)
    if product and (content_hash is None or product.get("hash") == content_hash):
        return product["data"]
    return None

def update_cache(sku, data, content_hash):
    """
    Update or add a product in the cache and write it to disk.
    """
    cache = load_cache()
    cache[sku] = {"hash": content_hash, "data": data}
    save_cache(cache)
