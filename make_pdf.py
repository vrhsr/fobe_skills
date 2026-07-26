import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Preformatted

def generate_pdf():
    pdf_filename = "Inventory_Reorder_Assessment_Submission.pdf"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_pdf_path = os.path.join(script_dir, pdf_filename)

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A2530"),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12
    )

    heading2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    heading3_style = ParagraphStyle(
        'Heading3Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1A202C"),
        backColor=colors.HexColor("#F7FAFC"),
        borderColor=colors.HexColor("#E2E8F0"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8
    )

    elements = []

    # Title Header
    elements.append(Paragraph("Inventory Reorder Alert System", title_style))
    elements.append(Paragraph("Python Intern Technical Assessment | Submission Report", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=12))

    # Submission Links Section (Featured Prominently)
    elements.append(Paragraph("Submission Links & Resources", heading2_style))
    links_text = (
        "<b>Live Interactive Streamlit App:</b> <font color='#2B6CB0'><u>https://fobeskills.streamlit.app/</u></font><br/>"
        "<b>GitHub Repository:</b> <font color='#2B6CB0'><u>https://github.com/vrhsr/fobe_skills</u></font><br/>"
        "<b>Backend Script:</b> <code>inventory_alert.py</code><br/>"
        "<b>Web UI Script:</b> <code>app.py</code>"
    )
    elements.append(Paragraph(links_text, body_style))
    elements.append(Spacer(1, 6))

    # Section 1: Overview & Approach
    elements.append(Paragraph("1. Assessment Summary & Technical Approach", heading2_style))
    approach_text = (
        "This submission implements an automated inventory alert system for daily warehouse management.<br/><br/>"
        "<b>Key Technical Highlights:</b><br/>"
        "• <b>File Handling & Structuring:</b> Reads CSV rows into clean Python dictionary structures using <code>csv.DictReader</code>.<br/>"
        "• <b>Priority Threshold Logic:</b> Items running below threshold are categorized into <code>CRITICAL</code> (stock &le; 25% of threshold) or <code>LOW</code> (stock &lt; threshold).<br/>"
        "• <b>Reorder Calculation:</b> Computes exact quantities needed to restock items back up to 80% of max capacity.<br/>"
        "• <b>Edge-Case Handling:</b> Gracefully handles missing quantities (defaulting to 0 with log warnings), blank threshold fields, and malformed rows without crashing.<br/>"
        "• <b>Multi-Format Output:</b> Formatted console log, simulated email alert, <code>restock_report.csv</code> export, and a live Streamlit dashboard with built-in sample data download."
    )
    elements.append(Paragraph(approach_text, body_style))
    elements.append(Spacer(1, 8))

    # Helper function to append code in chunks
    def append_code_chunks(filepath, title):
        elements.append(Paragraph(title, heading2_style))
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            chunk_size = 50
            for i in range(0, len(lines), chunk_size):
                chunk_text = "".join(lines[i:i+chunk_size])
                elements.append(Preformatted(chunk_text, code_style))
        else:
            elements.append(Paragraph("File not found.", body_style))
        elements.append(Spacer(1, 8))

    # Section 2: Core Script Code
    inventory_alert_path = os.path.join(script_dir, "inventory_alert.py")
    append_code_chunks(inventory_alert_path, "2. Backend Script (inventory_alert.py)")

    # Section 3: Web App Code
    app_path = os.path.join(script_dir, "app.py")
    append_code_chunks(app_path, "3. Streamlit Application Code (app.py)")

    # Section 4: Sample CSV Input
    stock_path = os.path.join(script_dir, "stock.csv")
    append_code_chunks(stock_path, "4. Input Stock Data (stock.csv)")

    # Section 5: Execution Output Log
    elements.append(Paragraph("5. Execution Output & Email Alert", heading2_style))
    sample_output = (
        "Loading stock data from: stock.csv\n"
        "Row 17 (Heavy Duty Shelf Labels): no quantity value, defaulting to 0.\n"
        "20 items loaded.\n\n"
        "========================================================================\n"
        "  INVENTORY REORDER REPORT\n"
        "  Generated : 2026-07-26  21:50:04\n"
        "  Scanned   : 20   |   Flagged : 16\n"
        "========================================================================\n\n"
        "  CRITICAL - Immediate action required (8 items)\n"
        "  ----------------------------------------------------------------------\n"
        "  [SKU-7002]  Surgical Masks\n"
        "    Stock    : 0 pack  (threshold: 100, max: 500)\n"
        "    Shortage : 100 pack below threshold\n"
        "    Reorder  : 400 pack (to reach 400 / 80% of capacity)\n\n"
        "  [SKU-7001]  Latex Gloves (Box)\n"
        "    Stock    : 3 box  (threshold: 50, max: 200)\n"
        "    Shortage : 47 box below threshold\n"
        "    Reorder  : 157 box (to reach 160 / 80% of capacity)\n\n"
        "--- SIMULATED EMAIL ALERT ---\n\n"
        "FROM    : alerts@inventory-system.com\n"
        "TO      : warehouse-manager@company.com\n"
        "SUBJECT : [RESTOCK ALERT] 8 Critical + 8 Low items need attention\n"
        "DATE    : Sunday, 26 July 2026 at 21:50\n\n"
        "------------------------------------------------------------\n"
        "Dear Warehouse Manager,\n\n"
        "Here is today's inventory scan report.\n"
        "As of Sunday, 26 July 2026 at 21:50, these items need to be restocked:\n\n"
        "  [CRITICAL]    Surgical Masks                  Stock:    0 / 100  -> Order: 400 pack\n"
        "  [CRITICAL]    Latex Gloves (Box)              Stock:    3 / 50   -> Order: 157 box\n"
        "  [CRITICAL]    Adhesive Labels                 Stock:   15 / 60   -> Order: 225 sheet\n"
        "  [CRITICAL]    Cardboard Boxes (L)             Stock:    9 / 50   -> Order: 191 unit\n"
        "  [LOW]         Cotton Fabric Roll              Stock:   18 / 60   -> Order: 222 roll\n"
        "  [LOW]         Steel Bolts (M6)                Stock:   42 / 80   -> Order: 278 pack\n\n"
        "Please contact suppliers to place the necessary orders.\n"
        "------------------------------------------------------------\n"
    )
    elements.append(Preformatted(sample_output, code_style))
    elements.append(Spacer(1, 8))

    # Section 6: Reflection Note
    elements.append(Paragraph("6. Reflection Note", heading2_style))
    reflection_text = (
        "With more time, there are five key improvements I would introduce:<br/><br/>"
        "1. <b>Automated Job Scheduling:</b> Configure cron jobs or Windows Task Scheduler to execute automated daily stock audits at 07:00.<br/>"
        "2. <b>Supplier REST EDI APIs:</b> Auto-trigger draft purchase orders for items reaching critical threshold status.<br/>"
        "3. <b>Historical Consumption Tracking:</b> Log daily stock snapshots into SQLite to calculate moving usage trends and dynamically adjust thresholds.<br/>"
        "4. <b>Active Alerting:</b> Connect <code>smtplib</code> or Slack webhooks for immediate notification delivery.<br/>"
        "5. <b>Enhanced Dashboard:</b> Expand Streamlit UI with supplier-level breakdown charts and stock depletion trends."
    )
    elements.append(Paragraph(reflection_text, body_style))

    doc.build(elements)
    print(f"PDF successfully built at: {output_pdf_path}")

if __name__ == "__main__":
    generate_pdf()
