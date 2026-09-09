"""Reproducible Group030 JSON/XML integration and validation workflow."""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from Group030_text_functions import (
    MISSING, _remove_emoji, build_latin_analysis, clean_delivery_note, clean_narrative_text,
    contains_non_latin_script, extract_order_reference,
    extract_product_sku, extract_promo_code,
)

GROUP_ID = "Group030"
TABLES = ["orders", "order_items", "customers", "deliveries", "products", "product_reviews"]


def money(value):
    if isinstance(value, (int, float)): return float(value)
    return float(re.sub(r"[^0-9.+-]", "", str(value).replace(",", "")))

def boolean(value):
    if isinstance(value, bool): return value
    v = str(value).strip().lower()
    if v in {"true", "t", "yes", "y", "1"}: return True
    if v in {"false", "f", "no", "n", "0"}: return False
    raise ValueError(f"Unrecognised boolean: {value!r}")

def text(value):
    v = "" if value is None else str(value).strip()
    return v if v else MISSING

def date(value, dayfirst=False):
    return pd.to_datetime(value, dayfirst=dayfirst).strftime("%Y-%m-%d")

def timestamp(value, dayfirst=False):
    return pd.to_datetime(value, dayfirst=dayfirst).strftime("%Y-%m-%d %H:%M:%S")

def xml_record(element):
    return {child.tag: child.text for child in element}

def normalise_order(h, source):
    get = (lambda a, b: h[a]) if source == "json" else (lambda a, b: h.findtext(b))
    raw_note = get("customerNote", "Customer_Note")
    discount_raw = get("couponDiscount", "Coupon_Discount")
    discount = float(discount_raw) if source == "json" else money(discount_raw)
    return {
        "order_id": text(get("orderID", "Order_ID")),
        "source_system_record_id": text(get("sourceSystemRecordID", "Source_System_Record_ID")),
        "customer_id": text(get("customerID", "Customer_ID")),
        "order_timestamp": timestamp(get("orderTimestamp", "Order_Timestamp"), source == "xml"),
        "sales_channel": text(get("salesChannel", "Sales_Channel")),
        "payment_method": text(get("paymentMethod", "Payment_Method")),
        "currency": text(get("currency", "Currency")),
        "nearest_warehouse": text(get("nearestWarehouse", "Nearest_Warehouse")),
        "order_status": text(get("orderStatus", "Order_Status")),
        "delivery_charges": round(money(get("deliveryCharges", "Delivery_Charges")), 2),
        "coupon_code": text(get("couponCode", "Coupon_Code")),
        "coupon_discount": discount,
        "season": text(get("season", "Season")),
        "expedited_delivery": boolean(get("expeditedDelivery", "Expedited_Delivery")),
        "customer_lat": float(get("customerLat", "Customer_Lat")),
        "customer_long": float(get("customerLong", "Customer_Long")),
        "device_type": text(get("deviceType", "Device_Type")),
        "referral_source": text(get("referralSource", "Referral_Source")),
        "customer_note_clean": clean_narrative_text(raw_note),
        "promo_code": extract_promo_code(raw_note),
    }

def normalise_item(item, source):
    get = (lambda a, b: item[a]) if source == "json" else (lambda a, b: item.findtext(b))
    qty = int(get("quantity", "Quantity")); price = money(get("unitPrice", "Unit_Price"))
    return {"order_item_id": text(get("orderItemID", "Order_Item_ID")),
            "order_id": text(get("orderID", "Order_ID")), "product_id": text(get("productID", "Product_ID")),
            "quantity": qty, "unit_price": round(price, 2), "line_revenue": round(qty * price, 2)}

def normalise_delivery(d, source):
    get = (lambda a, b: d[a]) if source == "json" else (lambda a, b: d.findtext(b))
    return {"delivery_id": text(get("deliveryID", "Delivery_ID")), "order_id": text(get("orderID", "Order_ID")),
      "dispatch_date": date(get("dispatchDate", "Dispatch_Date"), source == "xml"),
      "promised_date": date(get("promisedDate", "Promised_Date"), source == "xml"),
      "delivered_date": date(get("deliveredDate", "Delivered_Date"), source == "xml"),
      "carrier": text(get("carrier", "Carrier")), "service_level": text(get("serviceLevel", "Service_Level")),
      "delivery_status": text(get("deliveryStatus", "Delivery_Status")), "delay_days": int(get("delayDays", "Delay_Days")),
      "on_time_in_full": boolean(get("onTimeInFull", "On_Time_In_Full")),
      "fulfilment_hours": int(get("fulfilmentHours", "Fulfilment_Hours")),
      "delivery_cost": round(money(get("deliveryCost", "Delivery_Cost")), 2),
      "delay_reason": text(get("delayReason", "Delay_Reason")), "promised_days": int(get("promisedDays", "Promised_Days")),
      "tracking_event_count": int(get("trackingEventCount", "Tracking_Event_Count")),
      "delivery_window": text(get("deliveryWindow", "Delivery_Window")),
      "shipping_distance_km": float(get("shippingDistanceKm", "Shipping_Distance_Km")),
      "signature_required": boolean(get("signatureRequired", "Signature_Required")),
      "estimated_carbon_kg": float(get("estimatedCarbonKg", "Estimated_Carbon_Kg")),
      "delivery_note_clean": clean_delivery_note(get("deliveryNoteClean", "Delivery_Note_Clean"))}

def normalise_review(r, source):
    get = (lambda a, b: r[a]) if source == "json" else (lambda a, b: r.findtext(b))
    raw = get("reviewText", "Review_Text"); clean = clean_narrative_text(raw)
    return {"review_id": text(get("reviewID", "Review_ID")), "order_id": text(get("orderID", "Order_ID")),
      "order_item_id": text(get("orderItemID", "Order_Item_ID")), "product_id": text(get("productID", "Product_ID")),
      "customer_id": text(get("customerID", "Customer_ID")),
      "review_timestamp": timestamp(get("reviewTimestamp", "Review_Timestamp"), source == "xml"),
      "language_code": text(get("languageCode", "Language_Code")), "rating": int(get("rating", "Rating")),
      "review_title": text(get("reviewTitle", "Review_Title")), "review_body_clean": clean,
      "review_body_latin_analysis": build_latin_analysis(clean),
      "verified_purchase": boolean(get("verifiedPurchase", "Verified_Purchase")),
      "helpful_votes": int(get("helpfulVotes", "Helpful_Votes")),
      "review_length_chars": 0 if clean == MISSING else len(clean),
      "review_word_count": 0 if clean == MISSING else len(clean.split()),
      "contains_non_latin_script": contains_non_latin_script(clean),
      "extracted_order_reference": extract_order_reference(raw), "extracted_product_sku": extract_product_sku(raw),
      "delivery_experience": text(get("deliveryExperience", "Delivery_Experience")),
      "value_experience": text(get("valueExperience", "Value_Experience")),
      "writing_style": text(get("writingStyle", "Writing_Style"))}

def reconcile(records, key, table, conflicts):
    canonical = {}
    for source, row in records:
        k = row[key]
        if k not in canonical: canonical[k] = (row, {source})
        else:
            old, sources = canonical[k]
            differences = {}
            for field, new_value in row.items():
                old_value = old[field]
                old_missing = old_value is None or old_value == MISSING or pd.isna(old_value)
                new_missing = new_value is None or new_value == MISSING or pd.isna(new_value)
                if old_missing and not new_missing:
                    old[field] = new_value
                elif not old_missing and not new_missing and old_value != new_value:
                    differences[field] = (old_value, new_value)
            if differences:
                conflicts.append({"table": table, "key": k, "existing_sources": sorted(sources),
                                  "incoming_source": source, "differences": differences})
            sources.add(source)
    return [canonical[k][0] for k in sorted(canonical)]

def build_tables(input_dir, dictionary_path):
    with open(input_dir / f"{GROUP_ID}_commerce.json", encoding="utf-8") as f: js = json.load(f)
    root = ET.parse(input_dir / f"{GROUP_ID}_operations.xml").getroot()
    conflicts = []
    order_rows=[]; item_rows=[]; delivery_rows=[]; review_rows=[]
    for o in js["orders"]:
        order_rows.append(("JSON", normalise_order(o["header"], "json")))
        item_rows += [("JSON", normalise_item(x, "json")) for x in o["shoppingCart"]]
        if o.get("delivery"): delivery_rows.append(("JSON", normalise_delivery(o["delivery"], "json")))
    for o in root.findall("./Orders/Order"):
        order_rows.append(("XML", normalise_order(o.find("Header"), "xml")))
        item_rows += [("XML", normalise_item(x, "xml")) for x in o.findall("./Shopping_Cart/Item")]
        if o.find("Delivery") is not None: delivery_rows.append(("XML", normalise_delivery(o.find("Delivery"), "xml")))
    for r in js["productReviews"]: review_rows.append(("JSON", normalise_review(r, "json")))
    for r in root.findall("./ProductReviews/Review"): review_rows.append(("XML", normalise_review(r, "xml")))
    customer_rows=[]
    cmap={"customerID":"customer_id","signupDate":"signup_date","loyaltyTier":"loyalty_tier","customerSegment":"customer_segment","ageBand":"age_band","preferredChannel":"preferred_channel","homeSuburb":"home_suburb","prior12MOrders":"prior_12m_orders","lifetimeValueBeforePeriod":"lifetime_value_before_period","marketingConsent":"marketing_consent","homePostcode":"home_postcode","homeState":"home_state","homeCountry":"home_country","preferredLanguage":"preferred_language","acquisitionSource":"acquisition_source","accountStatus":"account_status","preferredDevice":"preferred_device","emailDomain":"email_domain","householdSizeBand":"household_size_band","contactFrequencyPreference":"contact_frequency_preference"}
    for x in js["customerProfiles"]:
        row={v:x[k] for k,v in cmap.items()}
        row["signup_date"]=date(row["signup_date"])
        row["prior_12m_orders"]=int(row["prior_12m_orders"])
        row["lifetime_value_before_period"]=round(money(row["lifetime_value_before_period"]),2)
        row["marketing_consent"]=boolean(row["marketing_consent"])
        for field in set(row)-{"prior_12m_orders","lifetime_value_before_period","marketing_consent"}:
            row[field]=text(row[field])
        customer_rows.append(("JSON",row))
    product_rows=[]
    pmap={"Product_ID":"product_id","Product_Name":"product_name","Category":"category","Brand":"brand","Unit_Price":"unit_price","Unit_Cost":"unit_cost","Launch_Year":"launch_year","Warranty_Months":"warranty_months","Weight_Kg":"weight_kg","Product_Sku":"product_sku","Subcategory":"subcategory","Model_Family":"model_family","Colour":"colour","Supplier_ID":"supplier_id","Supplier_Country":"supplier_country","Launch_Date":"launch_date","Tax_Category":"tax_category","Package_Type":"package_type","Recyclable_Packaging":"recyclable_packaging","Active_Flag":"active_flag","Product_Description":"product_description_clean"}
    for p in root.findall("./ProductCatalogue/Product"):
        x=xml_record(p); row={v:x.get(k) for k,v in pmap.items()}
        for f in ["unit_price","unit_cost"]: row[f]=round(money(row[f]),2)
        row["weight_kg"]=money(row["weight_kg"])
        for f in ["launch_year","warranty_months"]: row[f]=int(row[f])
        for f in ["recyclable_packaging","active_flag"]: row[f]=boolean(row[f])
        for f in set(row)-{"unit_price","unit_cost","weight_kg","launch_year","warranty_months","recyclable_packaging","active_flag","launch_date","product_description_clean"}:
            row[f]=text(row[f])
        row["launch_date"]=date(row["launch_date"], True)
        row["product_description_clean"]=clean_narrative_text(row["product_description_clean"])
        product_rows.append(("XML",row))
    tables={"orders":pd.DataFrame(reconcile(order_rows,"order_id","orders",conflicts)),
      "order_items":pd.DataFrame(reconcile(item_rows,"order_item_id","order_items",conflicts)),
      "customers":pd.DataFrame(reconcile(customer_rows,"customer_id","customers",conflicts)),
      "deliveries":pd.DataFrame(reconcile(delivery_rows,"delivery_id","deliveries",conflicts)),
      "products":pd.DataFrame(reconcile(product_rows,"product_id","products",conflicts)),
      "product_reviews":pd.DataFrame(reconcile(review_rows,"review_id","product_reviews",conflicts))}
    # Published arithmetic is derived from canonical item lines, not trusted source totals.
    sums=tables["order_items"].groupby("order_id",as_index=False).line_revenue.sum().rename(columns={"line_revenue":"order_price"})
    tables["orders"]=tables["orders"].merge(sums,on="order_id",validate="one_to_one")
    tables["orders"]["order_price"]=tables["orders"]["order_price"].round(2)
    tables["orders"]["tax_amount"]=(tables["orders"].order_price/11).round(2)
    tables["orders"]["order_total"]=(tables["orders"].order_price*(1-tables["orders"].coupon_discount/100)+tables["orders"].delivery_charges).round(2)
    dictionary=pd.read_csv(dictionary_path)
    for name,df in tables.items():
        cols=dictionary.loc[dictionary.output_table.eq(name)].sort_values("position").field_name.tolist()
        tables[name]=df[cols]
    source_key_sets={}
    for table, rows, key in [("orders",order_rows,"order_id"),("order_items",item_rows,"order_item_id"),("customers",customer_rows,"customer_id"),("deliveries",delivery_rows,"delivery_id"),("products",product_rows,"product_id"),("product_reviews",review_rows,"review_id")]:
        source_key_sets[table]={s:[row[key] for src,row in rows if src==s] for s in ["JSON","XML"]}
    duplicates={table:{src:len(keys)-len(set(keys)) for src,keys in sources.items()} for table,sources in source_key_sets.items()}
    overlap={table:len(set(sources["JSON"]) & set(sources["XML"])) for table,sources in source_key_sets.items()}
    key_flow={table:{"JSON rows":len(sources["JSON"]),"JSON unique":len(set(sources["JSON"])),
                     "XML rows":len(sources["XML"]),"XML unique":len(set(sources["XML"])),
                     "cross-source overlap":len(set(sources["JSON"]) & set(sources["XML"])),
                     "expected canonical":len(set(sources["JSON"]) | set(sources["XML"])),
                     "actual canonical":len(tables[table])}
              for table,sources in source_key_sets.items()}
    profile={"json":{"customers":len(js["customerProfiles"]),"orders":len(js["orders"]),
      "order_items":sum(len(x["shoppingCart"]) for x in js["orders"]),
      "deliveries":sum(bool(x.get("delivery")) for x in js["orders"]),"reviews":len(js["productReviews"])},
      "xml":{"orders":len(root.findall("./Orders/Order")),
      "order_items":len(root.findall("./Orders/Order/Shopping_Cart/Item")),
      "deliveries":len(root.findall("./Orders/Order/Delivery")),
      "products":len(root.findall("./ProductCatalogue/Product")),"reviews":len(root.findall("./ProductReviews/Review"))},
      "canonical":{k:len(v) for k,v in tables.items()}, "within_source_duplicates":duplicates,
      "cross_source_overlap":overlap, "key_flow":key_flow, "conflicts":conflicts}
    return tables, profile

def validate(tables, dictionary, profile):
    rows=[]
    def add(cid, check, passed, observed, resolution="None required"):
        rows.append({"validation_id":cid,"check":check,"status":"PASS" if passed else "FAIL","observed_result":str(observed),"resolution_or_interpretation":resolution})
    expected=set(TABLES); add("VAL-SCHEMA-01","All six required tables are present",set(tables)==expected,sorted(tables))
    for name,df in tables.items():
        exp=dictionary[dictionary.output_table.eq(name)].sort_values("position").field_name.tolist()
        add(f"VAL-SCHEMA-{TABLES.index(name)+2:02d}",f"{name} columns match dictionary order",list(df)==exp,f"{name}: {len(df)} rows, {len(df.columns)} ordered columns")
        pk={"orders":"order_id","order_items":"order_item_id","customers":"customer_id","deliveries":"delivery_id","products":"product_id","product_reviews":"review_id"}[name]
        add(f"VAL-PK-{TABLES.index(name)+1:02d}",f"{name} primary key is complete and unique",df[pk].notna().all() and df[pk].is_unique,f"{name}.{pk}: missing={df[pk].isna().sum()}, duplicates={df[pk].duplicated().sum()}")
        required=dictionary[(dictionary.output_table.eq(name)) & (~dictionary.nullable.astype(bool))].field_name
        blank=sum((df[f].astype(str).str.strip()=="").sum() for f in required)
        pandas_missing=sum(df[f].isna().sum() for f in required)
        allowed_literal_nan={"customer_note_clean","product_description_clean","delivery_note_clean",
                             "review_body_clean","review_body_latin_analysis","coupon_code","promo_code",
                             "extracted_order_reference","extracted_product_sku"}
        invalid_literal_nan=sum(df[f].astype(str).eq(MISSING).sum() for f in required if f not in allowed_literal_nan)
        missing_ok=blank==0 and pandas_missing==0 and invalid_literal_nan==0
        add(f"VAL-MISS-{TABLES.index(name)+1:02d}",f"{name} required and prescribed string values use the correct missing representation",missing_ok,
            f"empty={blank}, pandas missing={pandas_missing}, invalid literal NaN={invalid_literal_nan}")
        type_failures=[]
        for _,spec in dictionary[dictionary.output_table.eq(name)].iterrows():
            s=df[spec.field_name]; typ=spec.data_type
            if typ=="number": ok=pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s) and s.notna().all()
            elif typ=="boolean": ok=pd.api.types.is_bool_dtype(s) and s.notna().all()
            elif typ=="date": ok=s.astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all() and pd.to_datetime(s,errors="coerce").notna().all()
            elif typ=="datetime": ok=s.astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}").all() and pd.to_datetime(s,errors="coerce").notna().all()
            else: ok=s.map(lambda value:isinstance(value,str)).all() and s.notna().all()
            if not ok:type_failures.append(spec.field_name)
        add(f"VAL-TYPE-{TABLES.index(name)+1:02d}",f"{name} fields conform to dictionary data types",not type_failures,f"type failures={type_failures}")
    fks=[("orders","customer_id","customers","customer_id"),("order_items","order_id","orders","order_id"),("order_items","product_id","products","product_id"),("deliveries","order_id","orders","order_id"),("product_reviews","order_id","orders","order_id"),("product_reviews","order_item_id","order_items","order_item_id"),("product_reviews","product_id","products","product_id"),("product_reviews","customer_id","customers","customer_id")]
    for i,(ct,cf,pt,pf) in enumerate(fks,1):
        missing=set(tables[ct][cf])-set(tables[pt][pf]); add(f"VAL-FK-{i:02d}",f"{ct}.{cf} references {pt}.{pf}",not missing,f"orphan keys={len(missing)}")
    duplicate_counts=profile["within_source_duplicates"]
    add("VAL-DUP-01","Within-source duplicate primary keys are counted for all six tables",set(duplicate_counts)==set(TABLES) and all(v>=0 for x in duplicate_counts.values() for v in x.values()),duplicate_counts,"Duplicate rows are compared field by field and collapsed by primary key")
    expected_shared={"orders","order_items","deliveries","product_reviews"}
    overlap_ok=all(profile["cross_source_overlap"][t]>0 for t in expected_shared) and all(profile["cross_source_overlap"][t]==0 for t in set(TABLES)-expected_shared)
    add("VAL-OVERLAP-01","Cross-source overlap is measured separately from within-source duplication",overlap_ok,profile["cross_source_overlap"])
    add("VAL-CONFLICT-01","Overlapping normalised records contain no field conflicts",not profile["conflicts"],f"normalised cross-source conflicts={len(profile['conflicts'])}","Investigate every listed field conflict before submission")
    for i,table in enumerate(TABLES,1):
        flow=profile["key_flow"][table]
        passed=flow["actual canonical"]==flow["expected canonical"]
        add(f"VAL-FLOW-{i:02d}",f"{table} canonical keys equal the union of unique JSON/XML keys",passed,flow)
    lines=tables["order_items"]
    line_calc=(lines.quantity*lines.unit_price).round(2)
    add("VAL-ARITH-00","Line revenue equals rounded quantity multiplied by unit price",(lines.line_revenue-line_calc).abs().le(.01).all(),f"max difference={(lines.line_revenue-line_calc).abs().max():.4f}")
    items=tables["order_items"].groupby("order_id").line_revenue.sum().round(2)
    actual=tables["orders"].set_index("order_id").order_price
    add("VAL-ARITH-01","Order price equals sum of rounded line revenues",(actual-items).abs().le(.01).all(),f"max difference={(actual-items).abs().max():.4f}")
    o=tables["orders"]
    calc=(o.order_price*(1-o.coupon_discount/100)+o.delivery_charges).round(2)
    add("VAL-ARITH-02","Order total applies discount then delivery without adding GST",(o.order_total-calc).abs().le(.01).all(),f"max difference={(o.order_total-calc).abs().max():.4f}")
    add("VAL-ARITH-03","Tax is included GST equal to order_price/11",(o.tax_amount-o.order_price.div(11).round(2)).abs().le(.01).all(),"GST not added to total")
    numeric_ok=(o.order_price.ge(0)&o.delivery_charges.ge(0)&o.coupon_discount.between(0,100)&o.customer_lat.between(-90,90)&o.customer_long.between(-180,180)).all()
    add("VAL-RANGE-01","Order numeric values fall in sensible ranges",numeric_ok,"non-negative money; discount 0–100; valid coordinates")
    add("VAL-RANGE-02","Item quantity is positive and price non-negative",tables["order_items"].quantity.gt(0).all() and tables["order_items"].unit_price.ge(0).all(),f"min quantity={tables['order_items'].quantity.min()}, min price={tables['order_items'].unit_price.min()}")
    add("VAL-RANGE-03","Review rating is 1–5 and helpful votes non-negative",tables["product_reviews"].rating.between(1,5).all() and tables["product_reviews"].helpful_votes.ge(0).all(),f"rating={tables['product_reviews'].rating.min()}–{tables['product_reviews'].rating.max()}")
    categorical={"sales_channel":{"Web","Store","Mobile"},"currency":{"AUD"},"order_status":{"Completed"},"service_level":{"Express","Standard"},"delivery_status":{"Delivered"},"rating":{1,2,3,4,5}}
    cat_bad={f:sorted(set((tables["orders"] if f in tables["orders"] else tables["deliveries"] if f in tables["deliveries"] else tables["product_reviews"])[f])-allowed) for f,allowed in categorical.items()}
    add("VAL-CAT-01","Published structured categories use observed allowed vocabularies",all(not x for x in cat_bad.values()),cat_bad)
    d=tables["deliveries"].merge(o[["order_id","order_timestamp"]],on="order_id")
    # Dispatch is date-only, so compare calendar dates (same-day dispatch is valid).
    temporal=(pd.to_datetime(d.order_timestamp).dt.normalize()<=pd.to_datetime(d.dispatch_date)) & (pd.to_datetime(d.dispatch_date)<=pd.to_datetime(d.delivered_date))
    add("VAL-TIME-01","Order date <= dispatch <= delivered",temporal.all(),f"violations={(~temporal).sum()}")
    promised=(pd.to_datetime(d.dispatch_date)<=pd.to_datetime(d.promised_date)); delivered=pd.to_datetime(d.delivered_date); promised_date=pd.to_datetime(d.promised_date); expected_delay=(delivered-promised_date).dt.days.clip(lower=0)
    add("VAL-TIME-02","Promised date is not before dispatch",promised.all(),f"violations={(~promised).sum()}")
    delay_consistency=d.delay_days.eq(expected_delay) & d.on_time_in_full.eq(delivered.le(promised_date))
    add("VAL-TIME-03","Delay days and OTIF agree with promised/delivered dates",delay_consistency.all(),f"violations={(~delay_consistency).sum()}")
    promised_days=(pd.to_datetime(d.promised_date)-pd.to_datetime(d.dispatch_date)).dt.days
    add("VAL-TIME-03B","Promised days agree with dispatch and promised dates",d.promised_days.eq(promised_days).all(),f"violations={(~d.promised_days.eq(promised_days)).sum()}")
    rv=tables["product_reviews"].merge(o[["order_id","order_timestamp"]],on="order_id")
    rt=pd.to_datetime(rv.review_timestamp)>=pd.to_datetime(rv.order_timestamp)
    add("VAL-TIME-04","Review timestamp is not before order timestamp",rt.all(),f"violations={(~rt).sum()}")
    sentinel_fields=[("orders","coupon_code"),("orders","promo_code"),("product_reviews","extracted_order_reference"),("product_reviews","extracted_product_sku"),("product_reviews","review_body_latin_analysis")]
    empty=sum((tables[t][f].astype(str).str.strip()=="").sum() for t,f in sentinel_fields)
    add("VAL-TEXT-01","Prescribed missing strings use literal NaN, not empty",empty==0,f"empty prescribed strings={empty}")
    nonlatin=tables["product_reviews"].contains_non_latin_script
    add("VAL-TEXT-02","Multilingual reviews and non-Latin indicators are preserved",nonlatin.any(),f"non-Latin reviews={nonlatin.sum()} of {len(nonlatin)}")
    refs=tables["product_reviews"]
    order_pattern=r"^(?:NaN|[HC]ORD\d{6})$"; sku_pattern=r"^(?:NaN|SKU-[A-Z0-9]+)$"
    add("VAL-TEXT-03","Extracted order references follow bounded format",refs.extracted_order_reference.str.fullmatch(order_pattern).all(),f"invalid formats={(~refs.extracted_order_reference.str.fullmatch(order_pattern)).sum()}")
    add("VAL-TEXT-04","Extracted SKUs follow bounded format",refs.extracted_product_sku.str.fullmatch(sku_pattern).all(),f"invalid formats={(~refs.extracted_product_sku.str.fullmatch(sku_pattern)).sum()}")
    promo=tables["orders"].promo_code
    promo_pattern=r"^(?:NaN|B[1-5]SAVE-\d{2})$"
    add("VAL-TEXT-04B","Extracted promotion codes follow bounded format",promo.str.fullmatch(promo_pattern).all(),f"invalid formats={(~promo.str.fullmatch(promo_pattern)).sum()}")
    review_lengths=refs.review_body_clean.map(lambda x:0 if x==MISSING else len(x))
    add("VAL-TEXT-05","Review character counts derive from cleaned multilingual text",review_lengths.eq(refs.review_length_chars).all(),f"mismatches={(review_lengths!=refs.review_length_chars).sum()}")
    review_words=refs.review_body_clean.map(lambda x:0 if x==MISSING else len(x.split()))
    add("VAL-TEXT-06","Review word counts derive from cleaned multilingual text",review_words.eq(refs.review_word_count).all(),f"mismatches={(review_words!=refs.review_word_count).sum()}")
    latin_expected=refs.review_body_clean.map(build_latin_analysis)
    nonlatin_expected=refs.review_body_clean.map(contains_non_latin_script)
    add("VAL-TEXT-07","Latin analysis is derived from cleaned multilingual review text",latin_expected.eq(refs.review_body_latin_analysis).all(),f"mismatches={(latin_expected!=refs.review_body_latin_analysis).sum()}")
    add("VAL-TEXT-08","Non-Latin indicator is derived from cleaned multilingual review text",nonlatin_expected.eq(refs.contains_non_latin_script).all(),f"mismatches={(nonlatin_expected!=refs.contains_non_latin_script).sum()}")
    lowercase_fields=[("orders","customer_note_clean"),("products","product_description_clean"),("product_reviews","review_body_clean")]
    lowercase_failures=sum((tables[t][f]!=MISSING).mul(tables[t][f].ne(tables[t][f].str.lower())).sum() for t,f in lowercase_fields)
    add("VAL-TEXT-09","The three designated cleaned narratives are lower-case",lowercase_failures==0,f"non-lower-case values={lowercase_failures}")
    delivery_notes=tables["deliveries"].delivery_note_clean
    uppercase_delivery_notes=delivery_notes.map(lambda value:value!=MISSING and any(char.isupper() for char in value)).sum()
    add("VAL-TEXT-10","Delivery notes retain source letter case instead of being forced to lower-case",uppercase_delivery_notes>0,f"delivery notes retaining upper-case letters={uppercase_delivery_notes}","Observed upper-case letters provide evidence that the delivery-specific cleaner preserves source case")
    wrapper_residue=refs.review_body_clean.str.contains(r"(?i)\breference\s*:|\bsku\s*:",regex=True).sum()+refs.review_body_latin_analysis.str.contains(r"(?i)\breference\s*:|\bsku\s*:",regex=True).sum()
    add("VAL-TEXT-11","Published review reference wrappers are absent from both cleaned review fields",wrapper_residue==0,f"wrapper residues={wrapper_residue}")
    emoji_residue=sum(_remove_emoji(value)!=value for field in ["review_body_clean","review_body_latin_analysis"] for value in refs[field])
    add("VAL-TEXT-12","No supported removable emoji remain in either cleaned review field",emoji_residue==0,f"emoji residues={emoji_residue}")
    return pd.DataFrame(rows)

PROJECT_ROOT = Path.cwd()
if (PROJECT_ROOT / "assignment_materials" / "allocated_package").is_dir():
    DEFAULT_DATA_ROOT = PROJECT_ROOT / "assignment_materials" / "allocated_package"
    DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "processing" / "outputs"
else:
    DEFAULT_DATA_ROOT = PROJECT_ROOT
    DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"


def main(input_dir=None, output_dir=None, dictionary_path=None):
    input_dir = DEFAULT_DATA_ROOT / "raw_input" if input_dir is None else Path(input_dir)
    output_dir = DEFAULT_OUTPUT_DIR if output_dir is None else Path(output_dir)
    dictionary_path = DEFAULT_DATA_ROOT / "public_data_dictionary.csv" if dictionary_path is None else Path(dictionary_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    tables, profile = build_tables(input_dir, dictionary_path)
    dictionary = pd.read_csv(dictionary_path)
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{GROUP_ID}_{name}_standardised.csv", index=False, na_rep=MISSING)
    validations = validate(tables, dictionary, profile)
    validations.to_csv(output_dir / f"{GROUP_ID}_validation_register.csv", index=False)
    print(validations.to_string(index=False))
    print("\nRow counts:", {name: len(frame) for name, frame in tables.items()})
    if validations.status.eq("FAIL").any():
        raise SystemExit("Validation failures require investigation")
    return tables, validations, profile


if __name__ == "__main__" and "get_ipython" not in globals():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_DATA_ROOT / "raw_input")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DATA_ROOT / "public_data_dictionary.csv")
    args = parser.parse_args()
    main(args.input_dir, args.output_dir, args.dictionary)
