"""Make the completed mapping rules field-specific without changing its template rows."""
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAPPING_PATH = PROJECT_ROOT / "processing" / "mapping" / "Group030_source_to_target_mapping.csv"
DICTIONARY_PATH = PROJECT_ROOT / "assignment_materials" / "allocated_package" / "public_data_dictionary.csv"

mapping = pd.read_csv(MAPPING_PATH, keep_default_na=False)
dictionary = pd.read_csv(DICTIONARY_PATH)[["output_table", "field_name", "data_type"]]
mapping = mapping.rename(columns={"target_field": "field_name"})
mapping = mapping.drop(columns="data_type", errors="ignore").merge(
    dictionary, on=["output_table", "field_name"], how="left", validate="one_to_one"
)

identifiers = {
    "order_id", "order_item_id", "customer_id", "product_id", "delivery_id", "review_id",
    "source_system_record_id", "supplier_id", "product_sku", "home_postcode",
}
money_fields = {
    "order_price", "delivery_charges", "tax_amount", "order_total", "unit_price",
    "line_revenue", "lifetime_value_before_period", "delivery_cost", "unit_cost",
}
integer_fields = {
    "quantity", "prior_12m_orders", "delay_days", "fulfilment_hours", "promised_days",
    "tracking_event_count", "launch_year", "warranty_months", "rating", "helpful_votes",
    "review_length_chars", "review_word_count",
}
boolean_fields = {
    "expedited_delivery", "marketing_consent", "on_time_in_full", "signature_required",
    "recyclable_packaging", "active_flag", "verified_purchase", "contains_non_latin_script",
}
date_fields = {"signup_date", "dispatch_date", "promised_date", "delivered_date", "launch_date"}
datetime_fields = {"order_timestamp", "review_timestamp"}
clean_fields = {"customer_note_clean", "delivery_note_clean", "product_description_clean", "review_body_clean"}

special = {
    ("orders", "order_price"): "sum the reconciled rounded line_revenue values by order_id, then round to 2 decimals",
    ("orders", "tax_amount"): "calculate included GST as round(order_price / 11, 2); do not add it to order_total",
    ("orders", "order_total"): "calculate round(order_price * (1 - coupon_discount / 100) + delivery_charges, 2)",
    ("order_items", "line_revenue"): "calculate round(quantity * unit_price, 2) for each order item",
    ("orders", "promo_code"): "extract bounded B1SAVE- to B5SAVE- code from raw customer note before cleaning; uppercase or literal NaN",
    ("orders", "customer_note_clean"): "after promo extraction, decode entities, apply Unicode NFC, remove tags, listed markers, URLs, emoji and complete reference/promotion wrappers; collapse whitespace, trim, lowercase; literal NaN if empty",
    ("deliveries", "delivery_note_clean"): "decode entities, apply Unicode NFC, remove tags, listed markers, URLs, emoji and any complete reference/promotion wrapper; collapse whitespace, trim, lowercase; literal NaN if empty",
    ("products", "product_description_clean"): "decode entities, apply Unicode NFC, remove tags, listed markers, URLs, emoji and any complete reference/promotion wrapper; collapse whitespace, trim, lowercase; literal NaN if empty",
    ("product_reviews", "review_body_clean"): "after order/SKU extraction, decode entities, apply Unicode NFC, remove tags, listed markers, URLs, emoji and the complete review-reference/promotion wrappers; collapse whitespace, trim, lowercase; literal NaN if empty",
    ("product_reviews", "review_body_latin_analysis"): "derive from review_body_clean; retain Latin-script letters including diacritics plus applicable digits and punctuation; literal NaN if no Latin letter remains",
    ("product_reviews", "review_length_chars"): "count Python characters in review_body_clean; return 0 for the literal NaN sentinel",
    ("product_reviews", "review_word_count"): "count whitespace-separated tokens in review_body_clean; return 0 for the literal NaN sentinel",
    ("product_reviews", "contains_non_latin_script"): "test review_body_clean for any Unicode letter outside the Latin script; return Python boolean",
    ("product_reviews", "extracted_order_reference"): "extract bounded HORD/CORD plus exactly six digits from raw review before cleaning; uppercase or literal NaN",
    ("product_reviews", "extracted_product_sku"): "extract bounded SKU- plus ASCII letters/digits from raw review before cleaning; uppercase or literal NaN",
}


def transformation(row):
    key = (row.output_table, row.field_name)
    if key in special:
        return special[key]
    field = row.field_name
    if field in clean_fields:
        wrapper = "promotion wrapper" if field == "customer_note_clean" else "complete review reference wrapper" if field == "review_body_clean" else "applicable wrappers"
        return f"decode entities, apply Unicode NFC, remove tags, listed markers, URLs, emoji and {wrapper}; collapse whitespace, trim, lowercase; literal NaN if empty"
    if field in identifiers:
        return "trim surrounding whitespace; preserve identifier case and leading zeros; do not invent or lowercase the key"
    if field in datetime_fields:
        return "parse ISO JSON or day-first XML timestamp and format YYYY-MM-DD HH:MM:SS"
    if field in date_fields:
        return "parse ISO JSON or day-first XML date and format YYYY-MM-DD"
    if field in boolean_fields:
        return "retain JSON boolean or map XML Y/N to Python/CSV True or False"
    if field == "coupon_discount":
        return "retain JSON numeric percentage points or remove the XML % sign and convert to numeric percentage points"
    if field in money_fields:
        return "remove AUD label and thousands separators, convert to numeric, and round monetary value to 2 decimals"
    if field in integer_fields:
        return "convert the source value to an integer without changing its business meaning"
    if row.data_type == "number":
        return "remove any source unit label where applicable and convert to numeric without unnecessary rounding"
    if field in {"coupon_code"}:
        return "trim the structured coupon code, preserve its case, and use literal NaN when absent"
    return f"trim surrounding whitespace and preserve the supplied {field.replace('_', ' ')} spelling and category case"


def overlap_rule(row):
    if row.source_format == "both":
        return "normalise before comparing by table primary key; fill a missing value from the matching non-missing value; record differing non-missing values as conflicts; retain one canonical row"
    if row.source_format == "derived":
        return "derive from reconciled canonical inputs; compare repeated keyed results and record any differing non-missing value before retaining one row"
    return f"{row.source_format}-only field: compare any within-source repeated primary key field by field; fill complementary missing values and record differing non-missing values before retaining one row"


section = {
    "orders": "Section 4.8 orders",
    "order_items": "Section 4.9 order items",
    "customers": "Section 4.10 customers",
    "deliveries": "Section 4.11 deliveries",
    "products": "Section 4.12 products",
    "product_reviews": "Section 4.13 product reviews",
}

mapping["transformation_or_derivation"] = mapping.apply(transformation, axis=1)
mapping["overlap_or_conflict_rule"] = mapping.apply(overlap_rule, axis=1)
mapping["notebook_evidence"] = mapping.output_table.map(section) + "; Section 5 reconciliation; Section 6 executable VAL checks"
template_columns = [
    "mapping_id", "output_table", "target_field", "source_format", "json_source_path",
    "xml_source_path", "transformation_or_derivation", "overlap_or_conflict_rule", "notebook_evidence",
]
mapping = mapping.rename(columns={"field_name": "target_field"})[template_columns]
mapping.to_csv(MAPPING_PATH, index=False)
print(f"Updated {len(mapping)} mapping rows in {MAPPING_PATH}")
