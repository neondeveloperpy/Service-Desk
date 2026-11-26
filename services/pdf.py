
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable,
)

from config import DATA_DIR
from database.repositories import (
    get_document,
    get_business,
    get_customer,
    get_document_items,
)


# ==========================================================
# PDF SETTINGS
# ==========================================================

PAGE_SIZE = A4

DARK = colors.HexColor("#202938")
ACCENT = colors.HexColor("#4F46E5")
LIGHT_GREY = colors.HexColor("#F3F4F6")
MID_GREY = colors.HexColor("#6B7280")
BORDER = colors.HexColor("#E5E7EB")


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def safe_text(value):
    """
    Escape text before placing it inside a ReportLab Paragraph.

    This prevents characters such as < and > from being
    interpreted as formatting instructions.
    """

    return escape(str(value or ""))


def format_money(amount, currency="USD"):
    """Format an amount as a currency string."""

    symbols = {
        "USD": "$",
        "GBP": "£",
        "EUR": "€",
        "PKR": "Rs ",
        "CAD": "CA$",
    }

    symbol = symbols.get(currency, f"{currency} ")

    return f"{symbol}{float(amount or 0):,.2f}"


def get_styles():
    """Create reusable PDF text styles."""

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocumentTitle",
        parent=styles["Heading1"],
        fontSize=25,
        leading=30,
        textColor=DARK,
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=10,
        leading=14,
        textColor=DARK,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="SmallText",
        parent=styles["Normal"],
        fontSize=8,
        leading=12,
        textColor=MID_GREY,
    ))

    styles.add(ParagraphStyle(
        name="BodyTextCustom",
        parent=styles["Normal"],
        fontSize=9,
        leading=14,
        textColor=DARK,
    ))

    styles.add(ParagraphStyle(
        name="TableHeader",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.white,
    ))

    styles.add(ParagraphStyle(
        name="RightText",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        alignment=TA_RIGHT,
        textColor=DARK,
    ))

    return styles


# ==========================================================
# DOCUMENT HEADER
# ==========================================================

def build_header(business, document, styles):
    """Build the business and invoice heading."""

    elements = []

    logo_path = business["logo_path"]

    # Add the business logo if one exists.
    if logo_path and Path(logo_path).is_file():

        logo = Image(
            logo_path,
            width=35 * mm,
            height=20 * mm,
            kind="proportional",
        )

        elements.append(logo)
        elements.append(Spacer(1, 5 * mm))

    business_name = safe_text(business["name"])

    business_details = [
        f"<b>{business_name}</b>"
    ]

    if business["address"]:
        business_details.append(
            safe_text(business["address"]).replace("\n", "<br/>")
        )

    if business["email"]:
        business_details.append(
            safe_text(business["email"])
        )

    if business["phone"]:
        business_details.append(
            safe_text(business["phone"])
        )

    left_content = Paragraph(
        "<br/>".join(business_details),
        styles["BodyTextCustom"],
    )

    doc_type = document["doc_type"].upper()

    right_content = [
        Paragraph(doc_type, styles["DocumentTitle"]),
        Paragraph(
            f"<b>Number:</b> {safe_text(document['number'])}",
            styles["RightText"],
        ),
        Paragraph(
            f"<b>Date:</b> {safe_text(document['issue_date'])}",
            styles["RightText"],
        ),
    ]

    if document["due_date"]:
        right_content.append(
            Paragraph(
                f"<b>Due date:</b> {safe_text(document['due_date'])}",
                styles["RightText"],
            )
        )

    header_table = Table(
        [[left_content, right_content]],
        colWidths=[95 * mm, 75 * mm],
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    elements.append(header_table)

    elements.append(Spacer(1, 8 * mm))

    elements.append(HRFlowable(
        width="100%",
        thickness=1,
        color=BORDER,
    ))

    elements.append(Spacer(1, 8 * mm))

    return elements


# ==========================================================
# CUSTOMER DETAILS
# ==========================================================

def build_customer_section(customer, styles):
    """Display the customer information."""

    if not customer:
        return []

    details = [
        Paragraph("BILL TO", styles["SectionHeading"]),
        Paragraph(
            f"<b>{safe_text(customer['name'])}</b>",
            styles["BodyTextCustom"],
        ),
    ]

    if customer["address"]:
        details.append(
            Paragraph(
                safe_text(customer["address"]).replace("\n", "<br/>"),
                styles["BodyTextCustom"],
            )
        )

    if customer["email"]:
        details.append(
            Paragraph(
                safe_text(customer["email"]),
                styles["BodyTextCustom"],
            )
        )

    if customer["phone"]:
        details.append(
            Paragraph(
                safe_text(customer["phone"]),
                styles["BodyTextCustom"],
            )
        )

    return details


# ==========================================================
# DOCUMENT ITEMS TABLE
# ==========================================================

def build_items_table(items, currency, styles):
    """Create the invoice or quote item table."""

    data = [[
        Paragraph("DESCRIPTION", styles["TableHeader"]),
        Paragraph("QTY", styles["TableHeader"]),
        Paragraph("UNIT PRICE", styles["TableHeader"]),
        Paragraph("TOTAL", styles["TableHeader"]),
    ]]

    for item in items:

        data.append([
            Paragraph(
                safe_text(item["description"]),
                styles["BodyTextCustom"],
            ),
            Paragraph(
                str(item["quantity"]),
                styles["RightText"],
            ),
            Paragraph(
                format_money(item["unit_price"], currency),
                styles["RightText"],
            ),
            Paragraph(
                format_money(item["line_total"], currency),
                styles["RightText"],
            ),
        ])

    table = Table(
        data,
        colWidths=[82 * mm, 18 * mm, 35 * mm, 35 * mm],
        repeatRows=1,
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),

        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),

        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),

        ("LINEBELOW", (0, 1), (-1, -1), 0.5, BORDER),
    ]))

    return table


# ==========================================================
# TOTALS SECTION
# ==========================================================

def build_totals_section(document, styles):
    """Display subtotal, discount, tax and grand total."""

    currency = document["currency"]

    rows = [
        [
            Paragraph("Subtotal", styles["RightText"]),
            Paragraph(
                format_money(document["subtotal"], currency),
                styles["RightText"],
            ),
        ],
    ]

    discount = float(document["discount"] or 0)

    if discount:
        rows.append([
            Paragraph("Discount", styles["RightText"]),
            Paragraph(
                f"-{format_money(discount, currency)}",
                styles["RightText"],
            ),
        ])

    tax_rate = float(document["tax_rate"] or 0)

    if tax_rate:
        rows.append([
            Paragraph(
                f"Tax ({tax_rate:g}%)",
                styles["RightText"],
            ),
            Paragraph(
                format_money(document["tax_amount"], currency),
                styles["RightText"],
            ),
        ])

    rows.append([
        Paragraph("<b>TOTAL</b>", styles["RightText"]),
        Paragraph(
            f"<b>{format_money(document['total'], currency)}</b>",
            styles["RightText"],
        ),
    ])

    table = Table(
        rows,
        colWidths=[35 * mm, 35 * mm],
        hAlign="RIGHT",
    )

    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

        ("LINEABOVE", (0, -1), (-1, -1), 1, DARK),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_GREY),
    ]))

    return table


# ==========================================================
# NOTES AND PAYMENT INFORMATION
# ==========================================================

def build_footer_information(business, document, styles):
    """Display notes, payment methods and payment terms."""

    elements = []

    if document["notes"]:
        elements.append(
            Paragraph("NOTES", styles["SectionHeading"])
        )

        elements.append(
            Paragraph(
                safe_text(document["notes"]).replace("\n", "<br/>"),
                styles["BodyTextCustom"],
            )
        )

        elements.append(Spacer(1, 5 * mm))

    if document["payment_terms"]:
        elements.append(
            Paragraph("PAYMENT TERMS", styles["SectionHeading"])
        )

        elements.append(
            Paragraph(
                safe_text(document["payment_terms"]),
                styles["BodyTextCustom"],
            )
        )

        elements.append(Spacer(1, 5 * mm))

    if business["payment_methods"]:
        elements.append(
            Paragraph("PAYMENT METHODS", styles["SectionHeading"])
        )

        elements.append(
            Paragraph(
                safe_text(business["payment_methods"]).replace(
                    "\n", "<br/>"
                ),
                styles["BodyTextCustom"],
            )
        )

    return elements


# ==========================================================
# MAIN PDF GENERATOR
# ==========================================================

def generate_document_pdf(document_id, output_path=None):
    """
    Generate a PDF invoice or quote.

    Args:
        document_id: ID of the invoice or quote.
        output_path: Optional custom PDF save location.

    Returns:
        Path to the generated PDF.
    """

    # Retrieve the document.
    document = get_document(document_id)

    if not document:
        raise ValueError("Document not found.")

    # Retrieve associated business and customer.
    business = get_business(document["business_id"])

    if not business:
        raise ValueError("Business not found.")

    customer = None

    if document["customer_id"]:
        customer = get_customer(document["customer_id"])

    # Retrieve invoice or quote items.
    items = get_document_items(document_id)

    if not items:
        raise ValueError(
            "Cannot generate a PDF without document items."
        )

    # Create the output folder.
    output_dir = DATA_DIR / "generated_documents"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a default filename.
    if output_path is None:

        safe_number = "".join(
            character
            for character in document["number"]
            if character.isalnum() or character in "-_"
        )

        filename = f"{safe_number}.pdf"

        output_path = output_dir / filename

    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Set up the PDF document.
    pdf = SimpleDocTemplate(
        str(output_path),
        pagesize=PAGE_SIZE,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"{document['doc_type']} {document['number']}",
        author=business["name"],
    )

    styles = get_styles()

    # Build PDF content.
    elements = []

    elements.extend(
        build_header(business, document, styles)
    )

    elements.extend(
        build_customer_section(customer, styles)
    )

    elements.append(Spacer(1, 10 * mm))

    elements.append(
        build_items_table(
            items,
            document["currency"],
            styles,
        )
    )

    elements.append(Spacer(1, 5 * mm))

    elements.append(
        build_totals_section(document, styles)
    )

    elements.append(Spacer(1, 12 * mm))

    elements.extend(
        build_footer_information(
            business,
            document,
            styles,
        )
    )

    # Generate the actual PDF.
    pdf.build(elements)

    return output_path
