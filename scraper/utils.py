import re
import unicodedata
import colorsys

def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    trans = str.maketrans("åäö", "aao")
    text = text.translate(trans)
    text = unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode()
    return text.strip()

def extract_only_number_value(text):
    if not text:
        return ""
    cleaned = text.replace(" ", "").replace("\xa0", "")
    cleaned = cleaned.replace(",", ".")
    match = re.search(r"\d*\.?\d+", cleaned)
    return match.group(0) if match else ""

def extract_only_numbers(text):
    return "".join(filter(str.isdigit, str(text)))

def parse_value_unit(text):
    if not text:
        return "", ""
    text = str(text).replace(",", ".")
    match = re.search(r"([\d.]+)\s*([a-zA-ZåäöÅÄÖ%]*)", text)
    if match:
        value, unit = match.group(1), match.group(2)
        return value.strip(), unit.strip()
    return "", ""

def parse_measurements(matt_text):
    result = {}
    if not matt_text:
        return result
    lines = matt_text.split(",")
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        label = parts[0].capitalize()
        value, unit = "", ""
        if len(parts) > 1:
            value, unit = parse_value_unit(" ".join(parts[1:]))
        if label in ["Längd", "L"]:
            result["Längd (värde)"] = value
            result["Längd (enhet)"] = unit
        elif label in ["Bredd", "B"]:
            result["Bredd (värde)"] = value
            result["Bredd (enhet)"] = unit
        elif label in ["Höjd", "H"]:
            result["Höjd (värde)"] = value
            result["Höjd (enhet)"] = unit
        elif label in ["Djup", "D"]:
            result["Djup (värde)"] = value
            result["Djup (enhet)"] = unit
        elif label in ["Diameter", "Diam.", "Diam"]:
            result["Diameter (värde)"] = value
            result["Diameter (enhet)"] = unit
        else:
            result["Mått (text)"] = matt_text
    return result

def sort_products(data, sort_key="Namn"):
    return sorted(data, key=lambda x: x.get(sort_key, "").lower())

def pastel_gradient_color(seed, total, idx, sat=0.25, light=0.85):
    h = (seed + idx/float(max(total,1))) % 1.0
    r, g, b = colorsys.hls_to_rgb(h, light, sat)
    return f"{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"

def get_category_levels(row):
    return (
        row.get("Category", "") or row.get("category", ""),
        row.get("Subcategory", "") or row.get("subcategory", ""),
        row.get("Sub-Subcategory", "") or row.get("sub-subcategory", ""),
    )

def build_category_colors(data):
    parents = sorted(set(get_category_levels(row)[0] for row in data if get_category_levels(row)[0]))
    subcats = sorted(set((get_category_levels(row)[0], get_category_levels(row)[1]) for row in data if get_category_levels(row)[1]))
    subsubs = sorted(set(get_category_levels(row) for row in data if get_category_levels(row)[2]))

    parent_colors = {cat: pastel_gradient_color(0.05, len(parents), idx) for idx, cat in enumerate(parents)}
    subcat_colors = {cat: pastel_gradient_color(0.3, len(subcats), idx) for idx, cat in enumerate(subcats)}
    subsub_colors = {cat: pastel_gradient_color(0.6, len(subsubs), idx) for idx, cat in enumerate(subsubs)}

    def get_color(row):
        parent, sub, subsub = get_category_levels(row)
        if subsub and (parent, sub, subsub) in subsub_colors:
            return f"FF{subsub_colors[(parent, sub, subsub)]}"
        elif sub and (parent, sub) in subcat_colors:
            return f"FF{subcat_colors[(parent, sub)]}"
        elif parent and parent in parent_colors:
            return f"FF{parent_colors[parent]}"
        return "FFFFFFFF"
    return get_color