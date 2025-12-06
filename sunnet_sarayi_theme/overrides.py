import frappe
from erpnext.e_commerce.doctype.website_item.website_item import get_product_filter_data as core_filter_function

def get_product_filter_data_override(filters):
    """
    B2B için geliştirilmiş özel filtre davranışı:

    ✔ En az 1 varyant filtreye uyuyorsa → TEMPLATE listede görünür
    ✔ Stokta olmayanları gizle aktifse → varyant stok kontrolü yapılır
    ✔ Stokta olmayan ama siparişe açık varyantlar gösterilir
    ✔ Normal ürünler ERPNext standart mantığıyla devam eder
    """

    # Önce ERPNext'in kendi sonuçlarını al
    result = core_filter_function(filters)
    items = result.get("items", [])

    # Kullanıcı "Stokta Olanları Göster" seçmiş mi?
    show_only_in_stock = filters.get("in_stock", False)

    final_items = []

    for item in items:
        # Template değilse → normal şekilde ekle
        if not item.get("is_template"):
            final_items.append(item)
            continue

        template_code = item.get("item_code")

        # Template içindeki varyantları çek
        variants = frappe.get_all(
            "Item",
            filters={"variant_of": template_code},
            fields=["name", "item_name", "stock_uom"]
        )

        # Hiç varyant yoksa template eklenmez
        if not variants:
            continue

        # Variantların stoklarını kontrol et
        has_match = False
        for v in variants:
            qty = frappe.db.get_value("Bin", {"item_code": v.name}, "actual_qty") or 0

            if show_only_in_stock:
                # Stokta olmayan ama siparişi açık ürünler
                allow_oos = frappe.db.get_value("Item", v.name, "allow_backorder")

                if qty > 0 or allow_oos:
                    has_match = True
                    break
            else:
                # Stok filtresi yoksa → template görünmesi için varyant yeterli
                has_match = True
                break

        if has_match:
            final_items.append(item)

    result["items"] = final_items
    return result


# ERPNext fonksiyonunu override et
override = {
    "erpnext.e_commerce.doctype.website_item.website_item.get_product_filter_data": 
        "sunnet_sarayi_theme.overrides.get_product_filter_data_override"
}

