# Placeholder for deduplication, parsing, or other helpers
def deduplicate_products(products, key_fields=None):
    if not key_fields:
        key_fields = ["Namn", "Artikelnummer"]
    seen = set()
    deduped = []
    for prod in products:
        key = tuple(prod.get(field, "") for field in key_fields)
        if key not in seen:
            seen.add(key)
            deduped.append(prod)
    return deduped
