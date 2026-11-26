
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from database import repositories as repo
from database.db import get_connection


# ==========================================================
# MONEY HELPERS
# ==========================================================

TWO_PLACES = Decimal("0.01")


def money(value):
    """
    Convert a value into a Decimal rounded to two places.

    Decimal is safer than float for financial calculations.
    """

    return Decimal(str(value or 0)).quantize(
        TWO_PLACES,
        rounding=ROUND_HALF_UP
    )


# ==========================================================
# DOCUMENT NUMBERING
# ==========================================================

def generate_document_number(business_id, doc_type):
    """
    Generate a document number.

    Examples:
        INV-2026-00001
        QUO-2026-00002

    Invoice and quote numbers use different prefixes.
    """

    if doc_type not in ("invoice", "quote"):
        raise ValueError("Invalid document type.")

    prefix = "INV" if doc_type == "invoice" else "QUO"
    year = date.today().year

    with get_connection() as conn:

        last_id = conn.execute("""
            SELECT COALESCE(MAX(id), 0)
            FROM documents
            WHERE business_id = ?
              AND doc_type = ?
        """, (business_id, doc_type)).fetchone()[0]

    next_number = last_id + 1

    return f"{prefix}-{year}-{next_number:05d}"


# ==========================================================
# CALCULATIONS
# ==========================================================

def calculate_document_totals(
    items,
    discount=0,
    tax_rate=0
):
    """
    Calculate the financial totals for an invoice or quote.

    Discount is a fixed currency amount.
    Tax is a percentage applied after discount.

    Returns:
        subtotal
        discount
        taxable_amount
        tax_rate
        tax_amount
        total
    """

    subtotal = Decimal("0.00")

    for item in items:

        quantity = Decimal(str(item["quantity"]))
        unit_price = money(item["unit_price"])

        line_total = money(quantity * unit_price)

        subtotal += line_total

    subtotal = money(subtotal)

    discount = money(discount)

    # A discount cannot exceed the subtotal.
    discount = min(max(discount, Decimal("0.00")), subtotal)

    taxable_amount = money(subtotal - discount)

    tax_rate = Decimal(str(tax_rate or 0))

    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative.")

    tax_amount = money(
        taxable_amount * tax_rate / Decimal("100")
    )

    total = money(taxable_amount + tax_amount)

    return {
        "subtotal": subtotal,
        "discount": discount,
        "taxable_amount": taxable_amount,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "total": total,
    }


# ==========================================================
# RECALCULATE DOCUMENT
# ==========================================================

def recalculate_document(document_id):
    """
    Recalculate and save an invoice or quote.

    Call this whenever an item is added, edited or removed.
    """

    document = repo.get_document(document_id)

    if not document:
        raise ValueError("Document not found.")

    items = repo.get_document_items(document_id)

    totals = calculate_document_totals(
        items=items,
        discount=document["discount"],
        tax_rate=document["tax_rate"]
    )

    repo.update_document(
        document_id,
        subtotal=float(totals["subtotal"]),
        discount=float(totals["discount"]),
        tax_rate=float(totals["tax_rate"]),
        tax_amount=float(totals["tax_amount"]),
        total=float(totals["total"])
    )

    return totals


# ==========================================================
# CREATE INVOICE OR QUOTE
# ==========================================================

def create_new_document(
    business_id,
    doc_type,
    customer_id=None,
    issue_date=None,
    due_date="",
    discount=0,
    tax_rate=None,
    notes="",
    payment_terms=""
):
    """
    Create a new invoice or quote with an automatic number.

    The business's default tax rate and currency are used
    unless another tax rate is supplied.
    """

    business = repo.get_business(business_id)

    if not business:
        raise ValueError("Business not found.")

    if doc_type not in ("invoice", "quote"):
        raise ValueError("Document must be an invoice or quote.")

    if tax_rate is None:
        tax_rate = business["tax_rate"]

    number = generate_document_number(
        business_id,
        doc_type
    )

    document_id = repo.create_document(
        business_id=business_id,
        customer_id=customer_id,
        doc_type=doc_type,
        number=number,
        status="draft",
        issue_date=issue_date or date.today().isoformat(),
        due_date=due_date,
        currency=business["currency"],
        discount=discount,
        tax_rate=tax_rate,
        notes=notes,
        payment_terms=payment_terms
    )

    recalculate_document(document_id)

    return document_id


# ==========================================================
# DOCUMENT ITEM OPERATIONS
# ==========================================================

def add_item_to_document(
    document_id,
    description,
    quantity=1,
    unit_price=0,
    service_id=None
):
    """Add an item and recalculate the document."""

    document = repo.get_document(document_id)

    if not document:
        raise ValueError("Document not found.")

    quantity = Decimal(str(quantity))
    unit_price = money(unit_price)

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if unit_price < 0:
        raise ValueError("Price cannot be negative.")

    item_id = repo.add_document_item(
        document_id=document_id,
        description=description,
        quantity=float(quantity),
        unit_price=float(unit_price),
        service_id=service_id
    )

    recalculate_document(document_id)

    return item_id


def edit_document_item(item_id, **fields):
    """Edit an item and recalculate its parent document."""

    allowed_fields = {
        "description",
        "quantity",
        "unit_price"
    }

    fields = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not fields:
        return False

    with get_connection() as conn:
        item = conn.execute("""
            SELECT * FROM document_items
            WHERE id = ?
        """, (item_id,)).fetchone()

    if not item:
        return False

    if "quantity" in fields and Decimal(str(fields["quantity"])) <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if "unit_price" in fields:
        if money(fields["unit_price"]) < 0:
            raise ValueError("Price cannot be negative.")

    document_id = item["document_id"]

    updated = repo.update_document_item(
        item_id,
        **fields
    )

    if updated:
        recalculate_document(document_id)

    return updated


def remove_document_item(item_id):
    """Remove an item and recalculate the document."""

    with get_connection() as conn:
        item = conn.execute("""
            SELECT document_id
            FROM document_items
            WHERE id = ?
        """, (item_id,)).fetchone()

    if not item:
        return False

    document_id = item["document_id"]

    deleted = repo.delete_document_item(item_id)

    if deleted:
        recalculate_document(document_id)

    return deleted


# ==========================================================
# DISCOUNT AND TAX
# ==========================================================

def update_document_pricing(
    document_id,
    discount=None,
    tax_rate=None
):
    """
    Update the discount and/or tax rate.

    Both values are saved and the document is recalculated.
    """

    document = repo.get_document(document_id)

    if not document:
        raise ValueError("Document not found.")

    updates = {}

    if discount is not None:
        if money(discount) < 0:
            raise ValueError("Discount cannot be negative.")

        updates["discount"] = float(money(discount))

    if tax_rate is not None:
        if Decimal(str(tax_rate)) < 0:
            raise ValueError("Tax rate cannot be negative.")

        updates["tax_rate"] = float(tax_rate)

    if updates:
        repo.update_document(document_id, **updates)

    return recalculate_document(document_id)


# ==========================================================
# DOCUMENT STATUS
# ==========================================================

def mark_invoice_paid(document_id):
    """Mark an invoice as paid."""

    document = repo.get_document(document_id)

    if not document:
        raise ValueError("Document not found.")

    if document["doc_type"] != "invoice":
        raise ValueError("Only invoices can be marked as paid.")

    return repo.update_document(
        document_id,
        status="paid",
        paid_at=date.today().isoformat()
    )


def update_document_status(document_id, status):
    """Change a document's status."""

    document = repo.get_document(document_id)

    if not document:
        raise ValueError("Document not found.")

    allowed_statuses = {
        "draft",
        "sent",
        "paid",
        "overdue",
        "accepted",
        "rejected",
        "cancelled"
    }

    if status not in allowed_statuses:
        raise ValueError("Invalid document status.")

    if document["doc_type"] == "quote":
        allowed_statuses = {
            "draft", "sent", "accepted",
            "rejected", "cancelled"
        }

        if status not in allowed_statuses:
            raise ValueError("Invalid quote status.")

    if document["doc_type"] == "invoice" and status == "paid":
        return mark_invoice_paid(document_id)

    return repo.update_document(
        document_id,
        status=status
    )
