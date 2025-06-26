from .utils import extract_only_number_value, parse_value_unit, parse_measurements, extract_only_numbers
from .cache import get_cached_product, update_cache, hash_content
from exclusions import is_excluded
from bs4 import BeautifulSoup
import requests

def scrape_product(product_url):
    if is_excluded(product_url):
        return None
    soup = BeautifulSoup(requests.get(product_url).text, "html.parser")
    if not soup:
        return None
    short_desc = soup.select_one(".woocommerce-product-details__short-description")
    artikelnummer = ""
    if short_desc:
        strong = short_desc.find("strong")
        if strong:
            artikelnummer = strong.get_text(strip=True)
    artikelnummer = extract_only_numbers(artikelnummer)
    content_hash = hash_content(soup.prettify())
    cached = get_cached_product(artikelnummer, content_hash)
    if cached:
        return cached
    namn = ""
    selectors = [
        "h1.edgtf-single-product-title[itemprop='name']",
        "h1.product_title"
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            namn = el.get_text(strip=True)
            break
    pris_inkl_elem = soup.select_one(".product_price_in")
    pris_inkl = pris_inkl_elem.get_text(strip=True) if pris_inkl_elem else ""
    pris_inkl = extract_only_number_value(pris_inkl)
    pris_exkl_elem = soup.select_one(".product_price_ex")
    pris_exkl = pris_exkl_elem.get_text(strip=True) if pris_exkl_elem else ""
    pris_exkl = extract_only_number_value(pris_exkl)
    produktbild_url = ""
    img = soup.select_one(".woocommerce-product-gallery__image img")
    if img and img.get("src"):
        produktbild_url = img.get("src")
    more_info = soup.select_one('.product_more_info.vc_col-md-6')
    info_dict = {}
    if more_info:
        for p in more_info.find_all('p'):
            text = ''.join([elem if isinstance(elem, str) else elem.get_text() for elem in p.contents])
            for line in text.split('\n'):
                line = line.strip()
                if not line or ':' not in line:
                    continue
                label, value = line.split(':', 1)
                label = label.strip().capitalize()
                value = value.strip()
                info_dict[label] = value
    farg = info_dict.get('Färg', '')
    material = info_dict.get('Material', '')
    serie = info_dict.get('Serie', '')
    matt_text = info_dict.get('Mått', '') or info_dict.get('Mått (text)', '')
    diameter_text = info_dict.get('Diameter', '')
    kapacitet_text = info_dict.get('Kapacitet', '')
    volym_text = info_dict.get('Volym', '')
    djup_text = info_dict.get('Djup', '') or info_dict.get('D', '')
    mått_dict = parse_measurements(matt_text)
    diameter_v, diameter_e = parse_value_unit(diameter_text)
    if not diameter_v and mått_dict.get("Diameter (värde)"):
        diameter_v = mått_dict.get("Diameter (värde)")
        diameter_e = mått_dict.get("Diameter (enhet)")
    kap_v, kap_e = parse_value_unit(kapacitet_text)
    vol_v, vol_e = parse_value_unit(volym_text)
    längd_v, längd_e = mått_dict.get("Längd (värde)"), mått_dict.get("Längd (enhet)")
    bredd_v, bredd_e = mått_dict.get("Bredd (värde)"), mått_dict.get("Bredd (enhet)")
    höjd_v, höjd_e = mått_dict.get("Höjd (värde)"), mått_dict.get("Höjd (enhet)")
    djup_v, djup_e = "", ""
    if djup_text:
        djup_v, djup_e = parse_value_unit(djup_text)
    if not djup_v and mått_dict.get("Djup (värde)"):
        djup_v = mått_dict.get("Djup (värde)")
        djup_e = mått_dict.get("Djup (enhet)")
    data = {
        "Namn": namn,
        "Artikelnummer": artikelnummer,
        "Färg": farg,
        "Material": material,
        "Serie": serie,
        "Pris exkl. moms (värde)": pris_exkl,
        "Pris exkl. moms (enhet)": "kr" if pris_exkl else "",
        "Pris inkl. moms (värde)": pris_inkl,
        "Pris inkl. moms (enhet)": "kr" if pris_inkl else "",
        "Mått (text)": mått_dict.get("Mått (text)", matt_text),
        "Längd (värde)": längd_v,
        "Längd (enhet)": längd_e,
        "Bredd (värde)": bredd_v,
        "Bredd (enhet)": bredd_e,
        "Höjd (värde)": höjd_v,
        "Höjd (enhet)": höjd_e,
        "Djup (värde)": djup_v,
        "Djup (enhet)": djup_e,
        "Diameter (värde)": diameter_v,
        "Diameter (enhet)": diameter_e,
        "Kapacitet (värde)": kap_v,
        "Kapacitet (enhet)": kap_e,
        "Volym (värde)": vol_v,
        "Volym (enhet)": vol_e,
        "Produktbild-URL": produktbild_url,
        "Produkt-URL": product_url
    }
    update_cache(artikelnummer, data, content_hash)
    return data