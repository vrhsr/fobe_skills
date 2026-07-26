import csv
import os
import sys
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INPUT_FILE   = "stock.csv"
OUTPUT_FILE  = "restock_report.csv"
ALERT_EMAIL  = "warehouse-manager@company.com"
SENDER_EMAIL = "alerts@inventory-system.com"

CRITICAL_PCT = 0.25  # below 25% of threshold = critical
HEALTHY_PCT  = 0.80  # reorder target = 80% of max capacity


def load_stock(filepath):
    records = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path  = os.path.join(script_dir, filepath)

    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return records

    with open(full_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                row = {k: v.strip() for k, v in row.items() if k}

                if not row.get("item_name"):
                    print(f"Row {row_num}: missing item_name, skipped.")
                    continue

                qty_raw       = row.get("current_quantity", "").strip()
                threshold_raw = row.get("reorder_threshold", "").strip()
                capacity_raw  = row.get("max_capacity", "").strip()

                if qty_raw == "":
                    print(f"Row {row_num} ({row['item_name']}): no quantity value, defaulting to 0.")
                    current_qty = 0
                else:
                    current_qty = int(float(qty_raw))

                if threshold_raw == "":
                    print(f"Row {row_num} ({row['item_name']}): no threshold, skipped.")
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
                print(f"Row {row_num}: could not parse row - {e}. Skipped.")

    return records


def classify_item(item):
    qty    = item["current_qty"]
    thresh = item["threshold"]
    cap    = item["max_capacity"]

    if qty >= thresh:
        return None

    if qty <= thresh * CRITICAL_PCT:
        priority = "CRITICAL"
    else:
        priority = "LOW"

    healthy_target = int(cap * HEALTHY_PCT)
    reorder_qty    = max(0, healthy_target - qty)

    return {
        **item,
        "priority":    priority,
        "reorder_qty": reorder_qty,
        "shortage":    thresh - qty,
    }


def build_restock_list(records):
    flagged = []
    for item in records:
        result = classify_item(item)
        if result:
            flagged.append(result)

    flagged.sort(key=lambda x: (x["priority"] != "CRITICAL", -x["shortage"]))
    return flagged


def print_console_report(flagged, total):
    now   = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    width = 72

    print("\n" + "=" * width)
    print("  INVENTORY REORDER REPORT")
    print(f"  Generated : {now}")
    print(f"  Scanned   : {total}   |   Flagged : {len(flagged)}")
    print("=" * width)

    if not flagged:
        print("\n  All stock levels are within acceptable ranges.\n")
        print("=" * width + "\n")
        return

    critical_items = [i for i in flagged if i["priority"] == "CRITICAL"]
    low_items      = [i for i in flagged if i["priority"] == "LOW"]

    def print_section(items, label):
        if not items:
            return
        print(f"\n  {label} ({len(items)} item{'s' if len(items) > 1 else ''})")
        print("  " + "-" * (width - 2))
        for item in items:
            print(f"  [{item['sku']}]  {item['item_name']}")
            print(f"    Category : {item['category']}")
            print(f"    Stock    : {item['current_qty']} {item['unit']}  "
                  f"(threshold: {item['threshold']}, max: {item['max_capacity']})")
            print(f"    Supplier : {item['supplier']}")
            print(f"    Shortage : {item['shortage']} {item['unit']} below threshold")
            print(f"    Reorder  : {item['reorder_qty']} {item['unit']} "
                  f"(to reach {int(item['max_capacity'] * HEALTHY_PCT)} / 80% of capacity)")
            print()

    print_section(critical_items, "CRITICAL - Immediate action required")
    print_section(low_items,      "LOW - Restock soon")

    print("=" * width)
    print(f"  Report saved to: {OUTPUT_FILE}")
    print("=" * width + "\n")


def simulate_email_alert(flagged):
    now = datetime.now().strftime("%A, %d %B %Y at %H:%M")
    critical_count = sum(1 for i in flagged if i["priority"] == "CRITICAL")
    low_count      = sum(1 for i in flagged if i["priority"] == "LOW")

    subject = (
        f"[RESTOCK ALERT] {critical_count} Critical + {low_count} Low items "
        f"need attention - {datetime.now().strftime('%d %b %Y')}"
    )

    print("\n--- SIMULATED EMAIL ALERT ---\n")

    print(f"FROM    : {SENDER_EMAIL}")
    print(f"TO      : {ALERT_EMAIL}")
    print(f"SUBJECT : {subject}")
    print(f"DATE    : {now}")
    print()
    print("-" * 60)
    print("Dear Warehouse Manager,")
    print()
    print("Here is today's inventory scan report.")
    print(f"As of {now}, these items need to be restocked:")
    print()

    for item in flagged:
        priority_label = f"[{item['priority']}]"
        print(
            f"  {priority_label:<12}  "
            f"{item['item_name']:<30}  "
            f"Stock: {item['current_qty']:>4} / {item['threshold']}  "
            f"-> Order: {item['reorder_qty']} {item['unit']}"
        )

    print()
    print("Please contact suppliers to place the necessary orders.")
    print()
    print("-" * 60)
    print("Inventory Alert System  |  Do not reply to this email.")
    print("-" * 60)
    print()


def export_csv_report(flagged):
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, OUTPUT_FILE)

    fieldnames = [
        "priority", "sku", "item_name", "category",
        "current_qty", "reorder_threshold", "max_capacity",
        "shortage", "reorder_qty", "unit", "supplier",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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

    print(f"Restock report saved to: {output_path}")


def print_reflection():
    print("\n" + "-" * 72)
    print("  REFLECTION NOTE")
    print("-" * 72)
    print(
        "With more time, there are a few things I'd want to improve here.\n"
        "\n"
        "  1. Scheduling - right now you have to run this manually. I'd set\n"
        "     it up as a cron job or Windows Task Scheduler so it runs every\n"
        "     morning automatically and the team always has a fresh report.\n"
        "\n"
        "  2. Supplier integration - instead of just flagging items, the script\n"
        "     could connect to supplier APIs and raise a purchase order directly\n"
        "     for anything in the critical tier.\n"
        "\n"
        "  3. Trend tracking - logging stock levels daily to a simple SQLite\n"
        "     database would let you spot which items drain fastest and adjust\n"
        "     thresholds based on actual usage rather than guesswork.\n"
        "\n"
        "  4. Real alerts - replacing the printed email simulation with smtplib\n"
        "     or a Slack webhook so the right people are notified immediately.\n"
        "\n"
        "  5. A basic dashboard - a lightweight Flask page where managers can\n"
        "     check stock health without needing to read a CSV or run anything.\n"
    )
    print("-" * 72 + "\n")


def main():
    print("\nLoading stock data from:", INPUT_FILE)
    records = load_stock(INPUT_FILE)

    if not records:
        print("No valid records found. Exiting.")
        return

    print(f"{len(records)} items loaded.\n")

    flagged = build_restock_list(records)

    print_console_report(flagged, len(records))

    if flagged:
        simulate_email_alert(flagged)
        export_csv_report(flagged)

    print_reflection()


if __name__ == "__main__":
    main()
