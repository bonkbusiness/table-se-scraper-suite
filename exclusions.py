EXCLUDED_URL_PREFIXES = [
    "https://www.table.se/produkter/container/",
    "https://www.table.se/produkter/teknik/",
    "https://www.table.se/produkter/talt/",
    # Add more as needed
]

def is_excluded(url: str) -> bool:
    """Return True if the URL should be excluded based on the prefix list."""
    return any(url.startswith(prefix) for prefix in EXCLUDED_URL_PREFIXES)
