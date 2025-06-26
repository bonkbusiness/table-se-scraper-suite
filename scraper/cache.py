import json
import os
import hashlib
import shutil
import tempfile

CACHE_FILE = "product_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            backup_file = CACHE_FILE + ".corrupt"
            shutil.copy2(CACHE_FILE, backup_file)
            print(f"Warning: Cache file corrupted! Backup saved as {backup_file}. Starting with empty cache. ({e})")
            return {}
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {}
    return {}

def save_cache(cache):
    try:
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as tf:
            json.dump(cache, tf, ensure_ascii=False, indent=2)
            tempname = tf.name
        os.replace(tempname, CACHE_FILE)
    except Exception as e:
        print(f"Error saving cache: {e}")

def hash_content(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def get_cached_product(sku, content_hash=None):
    cache = load_cache()
    product = cache.get(sku)
    if product and (content_hash is None or product.get("hash") == content_hash):
        return product["data"]
    return None

def update_cache(sku, data, content_hash):
    if not sku:
        print("Warning: Tried to cache a product with empty SKU!")
        return
    cache = load_cache()
    cache[sku] = {"hash": content_hash, "data": data}
    print(f"Updating cache for SKU: {sku}")
    save_cache(cache)