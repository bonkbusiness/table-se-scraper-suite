import json
import os
import hashlib
import shutil
import tempfile

CACHE_FILE = "product_cache.json"

def load_cache():
    """
    Load the product cache from disk.
    If the cache is corrupted, back up the corrupted file and start with an empty cache.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            # Backup the corrupted file
            backup_file = CACHE_FILE + ".corrupt"
            shutil.copy2(CACHE_FILE, backup_file)
            print(f"Warning: Cache file corrupted! Backup saved as {backup_file}. Starting with empty cache. ({e})")
            return {}
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {}
    return {}

def save_cache(cache):
    """
    Save the product cache to disk using an atomic write to prevent corruption.
    """
    try:
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as tf:
            json.dump(cache, tf, ensure_ascii=False, indent=2)
            tempname = tf.name
        os.replace(tempname, CACHE_FILE)  # Atomic on most systems
    except Exception as e:
        print(f"Error saving cache: {e}")

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
