import re
import unicodedata
from typing import Optional, Any, Dict, List, Tuple
from html import unescape
import os
from datetime import datetime
from urllib.parse import urljoin

# --- Output Filename Utility ---

def make_output_filename(prefix: str, ext: str, folder: Optional[str] = None, timestamp: Optional[str] = None) -> str:
    """
    Return a standardized filename for output files.
    Args:
        prefix (str): Base name (e.g. 'products', 'errors', 'backup').
        ext (str): Extension, with or without dot (e.g. '.xlsx', 'csv', 'log', 'pkl', 'json').
        folder (str|None): Output folder. If None, auto-selects based on prefix.
        timestamp (str|None): Use this timestamp, or generate current one.
    Returns:
        str: Full file path.
    """
    if not ext.startswith('.'):
        ext = '.' + ext
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Auto-select folder if not explicitly specified
    if folder is None:
        if prefix in ('products', 'data'):
            folder = 'export'
        elif prefix in ('errors', 'error'):
            folder = 'error'
        elif prefix in ('log', 'logs', 'scrape'):
            folder = 'logs'
        elif prefix == 'backup':
            folder = 'backup'
        elif prefix == 'temp':
            folder = 'temp'
        else:
            folder = 'export'  # Default fallback

    filename = f"{prefix}_{timestamp}{ext}"
    path = os.path.join(folder, filename)
    os.makedirs(folder, exist_ok=True)
    return path

# --- Text Normalization and Cleaning ---

def normalize_text(text: Optional[str]) -> str:
    """Lowercase, remove accents, convert Swedish chars, and strip whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = text.replace("å", "a").replace("ä", "a").replace("ö", "o")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return text.strip()

def normalize_whitespace(text: Optional[str]) -> str:
    """Collapses multiple whitespace and trims the string."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def strip_html(text: Optional[str]) -> str:
    """
    Remove all HTML tags from a string. Also unescapes HTML entities.
    """
    if not text:
        return ""
    # Remove tags
    no_tags = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    return unescape(no_tags).strip()

# --- Number and Price Extraction ---

def extract_only_number_value(text: Optional[str]) -> str:
    """
    Extracts the first decimal number from a messy string as a string.
    Example: "1 234,00 kr" -> "1234.00"
    """
    if not text:
        return ""
    s = str(text).replace("\xa0", "").replace(" ", "")
    match = re.search(r"(\d{1,3}(?:[ \xa0]\d{3})*|\d+)([.,]\d+)?", s)
    if not match:
        return ""
    num = match.group(1).replace(" ", "")
    decimal = match.group(2) if match.group(2) else ""
    return f"{num}{decimal}".replace(",", ".")

def parse_price(text: Optional[str]) -> Optional[float]:
    """
    Extracts a price as a float from a string containing numbers, commas, dots, and currency symbols.
    Returns None if no valid number is found.
    Example: "1 234,50 kr" -> 1234.50
    """
    if not text:
        return None
    cleaned = re.sub(r"[^\d,.\-]", "", text.replace('\xa0', '').replace(' ', ''))
    if ',' in cleaned and '.' not in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None

def extract_only_numbers(text: Optional[str]) -> str:
    """
    Returns only the digits from a string.
    """
    if not text:
        return ""
    return "".join(re.findall(r"\d+", str(text)))

# --- Value and Unit Parsing ---

def parse_value_unit(text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Splits strings like '12 cm' into ('12', 'cm'), handling both decimal and integer values.
    Accepts both '12cm' and 'cm 12'.
    """
    if not text:
        return None, None
    m = re.match(r"([0-9.,\-]+)\s*([a-zA-Z%]+)", text.replace(",", "."))
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"([a-zA-Z%]+)\s*([0-9.,\-]+)", text.replace(",", "."))
    if m:
        return m.group(2), m.group(1)
    return None, None

def parse_measurements(matt_text: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Parses strings containing Swedish measurement labels into a dictionary of values and units.
    Example: "Längd: 120 cm, Bredd: 40 cm" → {
        "Längd (värde)": "120", "Längd (enhet)": "cm", ...
    }
    The measurement keys are kept in sync with scraper/product.py:
        - Längd (värde), Längd (enhet)
        - Bredd (värde), Bredd (enhet)
        - Höjd (värde), Höjd (enhet)
        - Djup (värde), Djup (enhet)
        - Diameter (värde), Diameter (enhet)
        - Kapacitet (värde), Kapacitet (enhet)
        - Volym (värde), Volym (enhet)
        - Vikt (värde), Vikt (enhet)
    """
    if not matt_text:
        return {}
    result = {}
    fields = re.split(r",|\n|;", matt_text)
    for field in fields:
        m = re.match(r"\s*([A-Za-zåäöÅÄÖ]+)\s*[:=]\s*([0-9.,\-]+)\s*([a-zA-Z%]*)", field.strip())
        if m:
            label = m.group(1).capitalize()
            value = m.group(2)
            unit = m.group(3)
            result[f"{label} (värde)"] = value
            result[f"{label} (enhet)"] = unit
    return result

# --- URL Utilities ---

def safe_urljoin(base: str, url: str) -> str:
    """Join a base URL and relative URL safely."""
    return urljoin(base, url)

def url_has_prefix(url: str, prefix: str) -> bool:
    """Check if the URL starts with prefix, case-insensitive."""
    return url.lower().startswith(prefix.lower())

def validate_url(url: Optional[str]) -> bool:
    """
    Checks if a string is a valid http(s) URL.
    """
    if not url:
        return False
    return bool(re.match(r'^https?://[^\s]+$', url.strip()))

# --- Tree Traversal Utilities ---

def traverse_tree(tree: List[Dict], get_children=lambda n: n.get("subs", [])):
    """
    Generator to traverse a tree structure. Yields each node.
    """
    for node in tree:
        yield node
        yield from traverse_tree(get_children(node), get_children)

# --- Duplicate Detection ---

def has_duplicates(items: List[Any]) -> bool:
    """Returns True if there are duplicates in the list."""
    return len(items) != len(set(items))

def deduplicate(items: List[Any]) -> List[Any]:
    """Remove duplicates while preserving order."""
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out

# --- Directory and File Utilities ---

def ensure_dir(path: str):
    """Ensure a directory exists, creating it if needed."""
    os.makedirs(path, exist_ok=True)

def current_timestamp(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """Return the current timestamp formatted as a string."""
    return datetime.now().strftime(fmt)

# --- ANSI Color and String Formatting ---

def color_text(text: str, color_code: str) -> str:
    """Wrap text in ANSI color codes."""
    RESET = "\033[0m"
    return f"{color_code}{text}{RESET}"

def format_multiline(text: str, line_prefix: str = "") -> str:
    """Prefix each line of a multi-line string with line_prefix."""
    return "\n".join(f"{line_prefix}{line}" for line in text.splitlines())

# --- Safe Nested Dict Access ---

def safe_get(d: Dict, *keys, default=None) -> Any:
    """
    Safely get a nested value from a dictionary. Returns default if any key is missing.
    Example: safe_get(product, 'foo', 'bar', default='N/A')
    """
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d

# --- BeautifulSoup Helpers ---

def safe_find_all(soup, tag, **kwargs):
    """Return [] if soup is None, else soup.find_all(tag, **kwargs)."""
    return soup.find_all(tag, **kwargs) if soup else []

# --- Sorting ---

def sort_products(data: List[Dict], sort_key="Namn") -> List[Dict]:
    """
    Sorts a list of dictionaries (e.g., products) by a given key, defaulting to 'Namn'.
    The sort_key should be one of the product export datapoints (see scraper/product.py).
    """
    return sorted(data, key=lambda x: x.get(sort_key, ""))

# --- Color Generation and Category Color Mapping (for visualization) ---

def pastel_gradient_color(level: int, total_levels: int = 3, sat: float = 0.25, light: float = 0.85) -> str:
    """
    Generates distinct pastel colors in hex along a hue gradient.
    """
    import colorsys
    hue = (level / max(total_levels, 1)) % 1.0
    r, g, b = colorsys.hls_to_rgb(hue, light, sat)
    return "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))

def get_category_levels(row: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Returns a tuple with category, subcategory, and sub-subcategory from a product dictionary.
    The preferred keys are "Kategori (parent)", "Kategori (sub)", but fallback to "Category", "Subcategory".
    """
    return (
        row.get("Kategori (parent)") or row.get("Category") or "",
        row.get("Kategori (sub)") or row.get("Subcategory") or "",
        row.get("Under-underkategori") or row.get("Subsubcategory") or "",
    )

def build_category_colors(data: List[Dict[str, Any]]):
    """
    Returns a function assigning a unique color to each product, based on its category hierarchy.
    Uses the "Kategori (parent)", "Kategori (sub)" keys as extracted in scraper/product.py.
    """
    cats = sorted({get_category_levels(row) for row in data})
    cat2idx = {c: i for i, c in enumerate(cats)}
    def get_color(row):
        idx = cat2idx.get(get_category_levels(row), 0)
        return pastel_gradient_color(idx, len(cat2idx))
    return get_color