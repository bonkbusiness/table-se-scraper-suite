from exclusions import is_excluded
from scraper.fetch import get_soup

def extract_product_data(product_url):
    """
    Extracts product data from a Table.se product page.
    Returns a dictionary with product fields, or None if excluded or failed.
    """
    if is_excluded(product_url):
        print(f"Skipping excluded product: {product_url}")
        return None
    soup = get_soup(product_url)
    if not soup:
        print(f"Failed to load product page: {product_url}")
        return None

    # Example parsing logic (customize fields as needed):
    product = {"Produkt-URL": product_url}

    # Name/title
    name_element = soup.select_one("h1.edgtf-single-product-title[itemprop='name'], h1.product_title")
    product["Namn"] = name_element.get_text(strip=True) if name_element else ""

    # Price (inkl. moms)
    price_inkl_elem = soup.select_one(".product_price_in")
    product["Pris inkl. moms (värde)"] = price_inkl_elem.get_text(strip=True) if price_inkl_elem else ""

    # Price (exkl. moms)
    price_exkl_elem = soup.select_one(".product_price_ex")
    product["Pris exkl. moms (värde)"] = price_exkl_elem.get_text(strip=True) if price_exkl_elem else ""

    # Article number
    short_desc = soup.select_one(".woocommerce-product-details__short-description strong")
    product["Artikelnummer"] = short_desc.get_text(strip=True) if short_desc else ""

    # Main image
    img = soup.select_one(".woocommerce-product-gallery__image img")
    product["Produktbild-URL"] = img['src'] if img and img.has_attr('src') else ""

    # Optional: parse additional info (color, material, etc.) as needed

    return product
