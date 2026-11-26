
from database.db import get_connection


# ==========================================================
# BUSINESSES
# ==========================================================

def create_business(
    name,
    email="",
    phone="",
    address="",
    currency="USD",
    tax_rate=0,
    logo_path="",
    payment_methods=""
):
    """Create a new business profile."""

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO businesses (
                name, email, phone, address,
                currency, tax_rate, logo_path,
                payment_methods
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email, phone, address,
            currency, tax_rate, logo_path,
            payment_methods
        ))

        return cursor.lastrowid


def get_business(business_id):
    """Get one business by ID."""

    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM businesses WHERE id = ?",
            (business_id,)
        ).fetchone()


def get_all_businesses():
    """Get all business profiles."""

    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM businesses ORDER BY name"
        ).fetchall()


def update_business(business_id, **fields):
    """Update selected business fields."""

    allowed_fields = {
        "name", "email", "phone", "address",
        "currency", "tax_rate", "logo_path",
        "payment_methods"
    }

    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not updates:
        return False

    columns = ", ".join(f"{key} = ?" for key in updates)

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE businesses SET {columns} WHERE id = ?",
            (*updates.values(), business_id)
        )

        return cursor.rowcount > 0


def delete_business(business_id):
    """Delete a business and its dependent records."""

    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM businesses WHERE id = ?",
            (business_id,)
        )

        return cursor.rowcount > 0


# ==========================================================
# CUSTOMERS
# ==========================================================

def create_customer(
    name,
    email="",
    phone="",
    address="",
    notes=""
):
    """Create a customer."""

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO customers (
                name, email, phone, address, notes
            )
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, phone, address, notes))

        return cursor.lastrowid


def get_customer(customer_id):
    """Get one customer."""

    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,)
        ).fetchone()


def get_all_customers():
    """Get all customers."""

    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM customers ORDER BY name"
        ).fetchall()


def search_customers(search_term):
    """Search customers by name, email or phone."""

    search = f"%{search_term}%"

    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM customers
            WHERE name LIKE ?
               OR email LIKE ?
               OR phone LIKE ?
            ORDER BY name
        """, (search, search, search)).fetchall()


def update_customer(customer_id, **fields):
    """Update selected customer fields."""

    allowed_fields = {
        "name", "email", "phone", "address", "notes"
    }

    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not updates:
        return False

    columns = ", ".join(f"{key} = ?" for key in updates)

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE customers SET {columns} WHERE id = ?",
            (*updates.values(), customer_id)
        )

        return cursor.rowcount > 0


def delete_customer(customer_id):
    """Delete a customer."""

    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM customers WHERE id = ?",
            (customer_id,)
        )

        return cursor.rowcount > 0


# ==========================================================
# SERVICES
# ==========================================================

def create_service(
    business_id,
    name,
    price,
    description=""
):
    """Create a reusable service for a business."""

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO services (
                business_id, name, price, description
            )
            VALUES (?, ?, ?, ?)
        """, (business_id, name, price, description))

        return cursor.lastrowid


def get_service(service_id):
    """Get one service."""

    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM services WHERE id = ?",
            (service_id,)
        ).fetchone()


def get_business_services(business_id):
    """Get all services belonging to a business."""

    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM services
            WHERE business_id = ?
            ORDER BY name
        """, (business_id,)).fetchall()


def update_service(service_id, **fields):
    """Update a service."""

    allowed_fields = {
        "name", "description", "price"
    }

    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not updates:
        return False

    columns = ", ".join(f"{key} = ?" for key in updates)

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE services SET {columns} WHERE id = ?",
            (*updates.values(), service_id)
        )

        return cursor.rowcount > 0


def delete_service(service_id):
    """Delete a reusable service."""

    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM services WHERE id = ?",
            (service_id,)
        )

        return cursor.rowcount > 0


# ==========================================================
# DOCUMENTS: INVOICES AND QUOTES
# ==========================================================

def create_document(
    business_id,
    doc_type,
    number,
    customer_id=None,
    status="draft",
    issue_date="",
    due_date="",
    currency="USD",
    subtotal=0,
    discount=0,
    tax_rate=0,
    tax_amount=0,
    total=0,
    notes="",
    payment_terms=""
):
    """Create an invoice or quote."""

    if doc_type not in ("invoice", "quote"):
        raise ValueError("Document type must be invoice or quote.")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO documents (
                business_id, customer_id, doc_type,
                number, status, issue_date, due_date,
                currency, subtotal, discount,
                tax_rate, tax_amount, total,
                notes, payment_terms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            business_id, customer_id, doc_type,
            number, status, issue_date, due_date,
            currency, subtotal, discount,
            tax_rate, tax_amount, total,
            notes, payment_terms
        ))

        return cursor.lastrowid


def get_document(document_id):
    """Get an invoice or quote."""

    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,)
        ).fetchone()


def get_business_documents(
    business_id,
    doc_type=None,
    status=None
):
    """Get documents belonging to a business."""

    query = """
        SELECT documents.*, customers.name AS customer_name
        FROM documents
        LEFT JOIN customers
            ON documents.customer_id = customers.id
        WHERE documents.business_id = ?
    """

    params = [business_id]

    if doc_type:
        query += " AND documents.doc_type = ?"
        params.append(doc_type)

    if status:
        query += " AND documents.status = ?"
        params.append(status)

    query += " ORDER BY documents.created_at DESC"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def update_document(document_id, **fields):
    """Update selected invoice or quote fields."""

    allowed_fields = {
        "customer_id", "status", "issue_date",
        "due_date", "currency", "subtotal",
        "discount", "tax_rate", "tax_amount",
        "total", "notes", "payment_terms",
        "email_sent_at", "paid_at"
    }

    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not updates:
        return False

    updates["updated_at"] = "CURRENT_TIMESTAMP"

    assignments = ", ".join(
        f"{key} = CURRENT_TIMESTAMP" if value == "CURRENT_TIMESTAMP"
        else f"{key} = ?"
        for key, value in updates.items()
    )

    params = [
        value for value in updates.values()
        if value != "CURRENT_TIMESTAMP"
    ]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE documents SET {assignments} WHERE id = ?",
            (*params, document_id)
        )

        return cursor.rowcount > 0


def delete_document(document_id):
    """Delete an invoice or quote."""

    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,)
        )

        return cursor.rowcount > 0


# ==========================================================
# DOCUMENT ITEMS
# ==========================================================

def add_document_item(
    document_id,
    description,
    quantity=1,
    unit_price=0,
    service_id=None
):
    """Add a service or custom item to a document."""

    line_total = float(quantity) * float(unit_price)

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO document_items (
                document_id, service_id,
                description, quantity,
                unit_price, line_total
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            document_id, service_id,
            description, quantity,
            unit_price, line_total
        ))

        return cursor.lastrowid


def get_document_items(document_id):
    """Get all items in an invoice or quote."""

    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM document_items
            WHERE document_id = ?
            ORDER BY id
        """, (document_id,)).fetchall()


def update_document_item(item_id, **fields):
    """Update an individual document item."""

    allowed_fields = {
        "description", "quantity", "unit_price"
    }

    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not updates:
        return False

    # Recalculate the line total when quantity or price changes.
    with get_connection() as conn:
        current = conn.execute(
            "SELECT * FROM document_items WHERE id = ?",
            (item_id,)
        ).fetchone()

        if not current:
            return False

        quantity = updates.get("quantity", current["quantity"])
        unit_price = updates.get("unit_price", current["unit_price"])

        updates["line_total"] = float(quantity) * float(unit_price)

        columns = ", ".join(f"{key} = ?" for key in updates)

        cursor = conn.execute(
            f"UPDATE document_items SET {columns} WHERE id = ?",
            (*updates.values(), item_id)
        )

        return cursor.rowcount > 0


def delete_document_item(item_id):
    """Delete an individual item."""

    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM document_items WHERE id = ?",
            (item_id,)
        )

        return cursor.rowcount > 0


# ==========================================================
# DOCUMENT NOTES
# ==========================================================

def add_document_note(document_id, body):
    """Add a comment or note to a document."""

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO document_notes (document_id, body)
            VALUES (?, ?)
        """, (document_id, body))

        return cursor.lastrowid


def get_document_notes(document_id):
    """Get all notes belonging to a document."""

    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM document_notes
            WHERE document_id = ?
            ORDER BY created_at DESC
        """, (document_id,)).fetchall()


def delete_document_note(note_id):
    """Delete a document note."""

    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM document_notes WHERE id = ?",
            (note_id,)
        )

        return cursor.rowcount > 0


# ==========================================================
# ATTACHMENTS
# ==========================================================

def add_attachment(document_id, filename, stored_path):
    """Save attachment information in the database."""

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO attachments (
                document_id, filename, stored_path
            )
            VALUES (?, ?, ?)
        """, (document_id, filename, stored_path))

        return cursor.lastrowid


def get_document_attachments(document_id):
    """Get all attachments for a document."""

    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM attachments
            WHERE document_id = ?
            ORDER BY uploaded_at DESC
        """, (document_id,)).fetchall()


def delete_attachment(attachment_id):
    """Delete an attachment database record."""

    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM attachments WHERE id = ?",
            (attachment_id,)
        )

        return cursor.rowcount > 0


# ==========================================================
# DASHBOARD AND ANALYTICS
# ==========================================================

def get_dashboard_stats(business_id):
    """Get basic sales and invoice statistics."""

    with get_connection() as conn:

        row = conn.execute("""
            SELECT

                COUNT(*) AS total_documents,

                SUM(
                    CASE
                        WHEN doc_type = 'invoice'
                        THEN 1 ELSE 0
                    END
                ) AS total_invoices,

                SUM(
                    CASE
                        WHEN doc_type = 'quote'
                        THEN 1 ELSE 0
                    END
                ) AS total_quotes,

                COALESCE(
                    SUM(
                        CASE
                            WHEN doc_type = 'invoice'
                            AND status = 'paid'
                            THEN total ELSE 0
                        END
                    ), 0
                ) AS paid_revenue,

                COALESCE(
                    SUM(
                        CASE
                            WHEN doc_type = 'invoice'
                            AND status != 'paid'
                            THEN total ELSE 0
                        END
                    ), 0
                ) AS outstanding_amount

            FROM documents
            WHERE business_id = ?

        """, (business_id,)).fetchone()

        return dict(row)


def get_recent_documents(business_id, limit=10):
    """Get the latest invoices and quotes."""

    with get_connection() as conn:
        return conn.execute("""
            SELECT
                documents.*,
                customers.name AS customer_name

            FROM documents

            LEFT JOIN customers
                ON documents.customer_id = customers.id

            WHERE documents.business_id = ?

            ORDER BY documents.created_at DESC

            LIMIT ?
        """, (business_id, limit)).fetchall()
