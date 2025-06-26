def check_field_completeness(products, required_fields=None):
    if not required_fields:
        required_fields = ["Namn", "Artikelnummer", "Pris inkl. moms (värde)", "Produkt-URL"]
    incomplete = []
    for prod in products:
        for field in required_fields:
            if not prod.get(field):
                incomplete.append(prod)
                break
    return incomplete
