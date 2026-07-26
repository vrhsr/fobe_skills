import streamlit as st
import pandas as pd
import csv
import io
from datetime import datetime

st.set_page_config(
    page_title="Inventory Reorder Alert System",
    page_icon="📦",
    layout="wide"
)

# ---- constants ----
CRITICAL_PCT = 0.25
HEALTHY_PCT  = 0.80

ALERT_EMAIL  = "warehouse-manager@company.com"
SENDER_EMAIL = "alerts@inventory-system.com"


# ---- core logic (same as inventory_alert.py) ----

def load_stock_from_file(uploaded_file):
    records = []
    warnings = []

    content = uploaded_file.read().decode("utf-8")
    reader  = csv.DictReader(io.StringIO(content))

    for row_num, row in enumerate(reader, start=2):
        try:
            row = {k: v.strip() for k, v in row.items() if k}

            if not row.get("item_name"):
                warnings.append(f"Row {row_num}: missing item_name, skipped.")
                continue

            qty_raw       = row.get("current_quantity", "").strip()
            threshold_raw = row.get("reorder_threshold", "").strip()
            capacity_raw  = row.get("max_capacity", "").strip()

            if qty_raw == "":
                warnings.append(f"Row {row_num} ({row['item_name']}): no quantity, defaulted to 0.")
                current_qty = 0
            else:
                current_qty = int(float(qty_raw))

            if threshold_raw == "":
                warnings.append(f"Row {row_num} ({row['item_name']}): no threshold, skipped.")
                continue
            threshold = int(float(threshold_raw))

            max_cap = int(float(capacity_raw)) if capacity_raw else threshold * 4

            records.append({
                "sku":          row.get("sku", "N/A"),
                "item_name":    row["item_name"],
                "category":     row.get("category", "General"),
                "current_qty":  current_qty,
                "threshold":    threshold,
                "max_capacity": max_cap,
                "unit":         row.get("unit", "unit"),
                "supplier":     row.get("supplier", "Unknown"),
            })

        except (ValueError, KeyError) as e:
            warnings.append(f"Row {row_num}: could not parse - {e}. Skipped.")

    return records, warnings


def classify_item(item):
    qty    = item["current_qty"]
    thresh = item["threshold"]
    cap    = item["max_capacity"]

    if qty >= thresh:
        return None

    priority = "CRITICAL" if qty <= thresh * CRITICAL_PCT else "LOW"

    healthy_target = int(cap * HEALTHY_PCT)
    reorder_qty    = max(0, healthy_target - qty)

    return {
        **item,
        "priority":    priority,
        "reorder_qty": reorder_qty,
        "shortage":    thresh - qty,
    }


def build_restock_list(records):
    flagged = [classify_item(i) for i in records]
    flagged = [i for i in flagged if i is not None]
    flagged.sort(key=lambda x: (x["priority"] != "CRITICAL", -x["shortage"]))
    return flagged


def build_email_text(flagged):
    now = datetime.now().strftime("%A, %d %B %Y at %H:%M")
    critical_count = sum(1 for i in flagged if i["priority"] == "CRITICAL")
    low_count      = sum(1 for i in flagged if i["priority"] == "LOW")

    subject = (
        f"[RESTOCK ALERT] {critical_count} Critical + {low_count} Low items "
        f"need attention - {datetime.now().strftime('%d %b %Y')}"
    )

    lines = [
        f"FROM    : {SENDER_EMAIL}",
        f"TO      : {ALERT_EMAIL}",
        f"SUBJECT : {subject}",
        f"DATE    : {now}",
        "",
        "-" * 60,
        "Dear Warehouse Manager,",
        "",
        "Here is today's inventory scan report.",
        f"As of {now}, these items need to be restocked:",
        "",
    ]

    for item in flagged:
        label = f"[{item['priority']}]"
        lines.append(
            f"  {label:<12}  "
            f"{item['item_name']:<30}  "
            f"Stock: {item['current_qty']:>4} / {item['threshold']}  "
            f"-> Order: {item['reorder_qty']} {item['unit']}"
        )

    lines += [
        "",
        "Please contact suppliers to place the necessary orders.",
        "",
        "-" * 60,
        "Inventory Alert System  |  Do not reply to this email.",
        "-" * 60,
    ]

    return "\n".join(lines)


def to_csv_bytes(flagged):
    output = io.StringIO()
    fieldnames = [
        "priority", "sku", "item_name", "category",
        "current_qty", "reorder_threshold", "max_capacity",
        "shortage", "reorder_qty", "unit", "supplier",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for item in flagged:
        writer.writerow({
            "priority":          item["priority"],
            "sku":               item["sku"],
            "item_name":         item["item_name"],
            "category":          item["category"],
            "current_qty":       item["current_qty"],
            "reorder_threshold": item["threshold"],
            "max_capacity":      item["max_capacity"],
            "shortage":          item["shortage"],
            "reorder_qty":       item["reorder_qty"],
            "unit":              item["unit"],
            "supplier":          item["supplier"],
        })
    return output.getvalue().encode("utf-8")


# ---- UI ----

st.title("Inventory Reorder Alert System")
st.caption("Upload your stock CSV to scan for items that need restocking.")

st.divider()

uploaded = st.file_uploader("Upload stock.csv", type=["csv"])

if not uploaded:
    st.info("Upload a CSV file with columns: sku, item_name, category, current_quantity, reorder_threshold, max_capacity, unit, supplier")
    st.stop()

records, warnings = load_stock_from_file(uploaded)

if warnings:
    with st.expander(f"Parse warnings ({len(warnings)})"):
        for w in warnings:
            st.warning(w)

if not records:
    st.error("No valid records found in the file.")
    st.stop()

flagged = build_restock_list(records)

critical_items = [i for i in flagged if i["priority"] == "CRITICAL"]
low_items      = [i for i in flagged if i["priority"] == "LOW"]
ok_count       = len(records) - len(flagged)

# ---- summary metrics ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Items",    len(records))
col2.metric("OK",             ok_count)
col3.metric("Low Stock",      len(low_items))
col4.metric("Critical",       len(critical_items), delta=f"-{len(critical_items)}" if critical_items else None, delta_color="inverse")

st.divider()

if not flagged:
    st.success("All stock levels are within acceptable ranges.")
    st.stop()

# ---- restock table ----
st.subheader("Items Needing Restock")

df = pd.DataFrame([{
    "Priority":   i["priority"],
    "SKU":        i["sku"],
    "Item":       i["item_name"],
    "Category":   i["category"],
    "Stock":      i["current_qty"],
    "Threshold":  i["threshold"],
    "Max Cap.":   i["max_capacity"],
    "Shortage":   i["shortage"],
    "Reorder Qty": i["reorder_qty"],
    "Unit":       i["unit"],
    "Supplier":   i["supplier"],
} for i in flagged])

def highlight_priority(row):
    if row["Priority"] == "CRITICAL":
        return ["background-color: #fde8e8; color: #c0392b; font-weight: 600"] * len(row)
    elif row["Priority"] == "LOW":
        return ["background-color: #fef9e7; color: #b7770d; font-weight: 600"] * len(row)
    return [""] * len(row)

styled = df.style.apply(highlight_priority, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ---- download button ----
st.download_button(
    label="Download restock_report.csv",
    data=to_csv_bytes(flagged),
    file_name="restock_report.csv",
    mime="text/csv",
)

st.divider()

# ---- simulated email ----
st.subheader("Simulated Email Alert")
email_text = build_email_text(flagged)
st.code(email_text, language=None)

st.divider()

# ---- reflection ----
with st.expander("Reflection note"):
    st.markdown("""
With more time, there are a few things I'd want to improve here.

1. **Scheduling** — right now you have to run this manually. I'd set it up as a cron job or Windows Task Scheduler so it runs every morning automatically.

2. **Supplier integration** — instead of just flagging items, the script could connect to supplier APIs and raise a purchase order directly for anything critical.

3. **Trend tracking** — logging stock levels daily to a SQLite database would let you spot which items drain fastest and adjust thresholds based on actual usage.

4. **Real alerts** — replacing the printed email simulation with smtplib or a Slack webhook so the right people are notified immediately.

5. **Better dashboard** — this Streamlit app is a start, but with more time I'd add historical charts and per-supplier order summaries.
""")
