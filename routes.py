
from fasthtml.common import *
from database import repositories as repo
from services import documents as document_service

from database.db import get_connection
from ui.layout import app_layout
from datetime import date
from ui.components import (
    button,
    card,
    stat_card,
    page_header,
    status_badge,
    empty_state,
    data_table,
)




# ==================================================
# DATABASE HELPERS
# ==================================================

def fetch_all(query, params=()):
    """Run a query and return rows as dictionaries."""

    with get_connection() as conn:
        cursor = conn.execute(query, params)
        columns = [column[0] for column in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def fetch_one(query, params=()):
    """Run a query and return one dictionary."""

    with get_connection() as conn:
        cursor = conn.execute(query, params)
        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))


def get_value(row, *keys, default=""):
    """Return the first available value from a row."""

    for key in keys:
        value = row.get(key)
        if value is not None:
            return value

    return default


def money(value, currency="USD"):
    """Format a monetary value."""

    symbols = {
        "USD": "$",
        "GBP": "£",
        "EUR": "€",
        "PKR": "Rs ",
    }

    symbol = symbols.get(currency, currency + " ")

    return f"{symbol}{float(value or 0):,.2f}"


# ==================================================
# DASHBOARD
# ==================================================

def dashboard_page():

    stats = fetch_one("""
        SELECT
            COUNT(CASE
                WHEN doc_type = 'invoice'
                THEN 1
            END) AS invoice_count,

            COUNT(CASE
                WHEN doc_type = 'quote'
                THEN 1
            END) AS quote_count,

            COALESCE(SUM(CASE
                WHEN doc_type = 'invoice'
                AND status = 'paid'
                THEN total
                ELSE 0
            END), 0) AS revenue,

            COALESCE(SUM(CASE
                WHEN doc_type = 'invoice'
                AND status NOT IN ('paid', 'cancelled')
                THEN total
                ELSE 0
            END), 0) AS outstanding

        FROM documents
    """)

    stats = stats or {}

    recent_documents = fetch_all("""
        SELECT *
        FROM documents
        ORDER BY created_at DESC
        LIMIT 5
    """)

    recent_rows = []

    for doc in recent_documents:
        customer = None

        if doc.get("customer_id"):
            customer = fetch_one(
                "SELECT * FROM customers WHERE id = ?",
                (doc["customer_id"],)
            )

        customer_name = (
            get_value(customer, "name", "full_name", default="Unknown")
            if customer else "No customer"
        )

        recent_rows.append([
            A(doc["number"], href=f"/documents/{doc['id']}"),
            customer_name,
            doc["doc_type"].capitalize(),
            money(doc["total"], doc.get("currency", "USD")),
            status_badge(doc["status"]),
        ])

    return app_layout(
        page_header(
            "Dashboard",
            "Here's an overview of your business."
        ),

        Div(
            stat_card(
                "Total Revenue",
                money(stats.get("revenue")),
                icon="↗"
            ),

            stat_card(
                "Outstanding",
                money(stats.get("outstanding")),
                icon="◷"
            ),

            stat_card(
                "Invoices",
                stats.get("invoice_count", 0),
                icon="▤"
            ),

            stat_card(
                "Quotes",
                stats.get("quote_count", 0),
                icon="▧"
            ),

            cls="stats-grid"
        ),

        card(
            data_table(
                ["Document", "Customer", "Type", "Amount", "Status"],
                recent_rows,
                empty_message="Your documents will appear here."
            ),
            title="Recent documents",
            description="Your latest invoices and quotes"
        ),

        active_page="dashboard",
        page_title="Dashboard"
    )


# ==================================================
# INVOICES AND QUOTES
# ==================================================

def document_list_page(doc_type):

    documents = fetch_all("""
        SELECT *
        FROM documents
        WHERE doc_type = ?
        ORDER BY created_at DESC
    """, (doc_type,))

    rows = []

    for doc in documents:
        customer = None

        if doc.get("customer_id"):
            customer = fetch_one(
                "SELECT * FROM customers WHERE id = ?",
                (doc["customer_id"],)
            )

        customer_name = (
            get_value(customer, "name", "full_name", default="Unknown")
            if customer else "No customer"
        )

        rows.append([
            A(doc["number"], href=f"/documents/{doc['id']}"),
            customer_name,
            doc.get("issue_date", ""),
            money(doc.get("total"), doc.get("currency", "USD")),
            status_badge(doc.get("status", "draft")),
        ])

    title = "Invoices" if doc_type == "invoice" else "Quotes"
    active_page = doc_type + "s"

    return app_layout(
        page_header(
            title,
            f"Manage your {doc_type}s.",
            actions=[
                A(
                    button("＋ New " + doc_type),
                    href=f"/{doc_type}s/new"
                )
            ]
        ),

        card(
            data_table(
                [
                    "Document",
                    "Customer",
                    "Issue date",
                    "Amount",
                    "Status"
                ],
                rows,
                empty_message=f"No {doc_type}s have been created yet."
            )
        ),

        active_page=active_page,
        page_title=title
    )


# ==================================================
# CUSTOMERS
# ==================================================

def customers_page():

    customers = fetch_all("""
        SELECT *
        FROM customers
        ORDER BY id DESC
    """)

    rows = []

    for customer in customers:
        rows.append([
            get_value(customer, "name", "full_name", "company"),
            get_value(customer, "email"),
            get_value(customer, "phone"),
            get_value(customer, "address"),
        ])

    return app_layout(
        page_header(
            "Customers",
            "Manage your customer information.",
            actions=[
                A(
                    button("＋ Add customer"),
                    href="/customers/new"
                )
            ]
        ),

        card(
            data_table(
                ["Name", "Email", "Phone", "Address"],
                rows,
                empty_message="You haven't added any customers yet."
            )
        ),

        active_page="customers",
        page_title="Customers"
    )


# ==================================================
# SERVICES
# ==================================================

def services_page():

    services = fetch_all("""
        SELECT *
        FROM services
        ORDER BY id DESC
    """)

    rows = []

    for service in services:
        rows.append([
            get_value(service, "name", "title", "service_name"),
            get_value(service, "description"),
            money(get_value(service, "price", "unit_price", "rate")),
        ])

    return app_layout(
        page_header(
            "Services",
            "Manage your reusable services and prices.",
            actions=[
                A(
                    button("＋ Add service"),
                    href="/services/new"
                )
            ]
        ),

        card(
            data_table(
                ["Service", "Description", "Price"],
                rows,
                empty_message="You haven't added any services yet."
            )
        ),

        active_page="services",
        page_title="Services"
    )


# ==================================================
# SETTINGS
# ==================================================

def settings_page():

    businesses = fetch_all("""
        SELECT *
        FROM businesses
        ORDER BY id DESC
    """)

    
    rows = []

    for business in businesses:
        rows.append([
            A(
                business["name"],
                href=f"/settings/businesses/{business['id']}/payments"
            ),
            get_value(business, "email"),
            get_value(business, "phone"),
            get_value(business, "currency"),
            A(
                "Payment settings",
                href=f"/settings/businesses/{business['id']}/payments"
            )
        ])

    return app_layout(
        page_header(
            "Settings",
            "Manage your business profiles and preferences.",
            actions=[
                A(
                    button("＋ Add business"),
                    href="/settings/businesses/new"
                )
            ]
        ),

        card(
            data_table(
                ["Business", "Email", "Phone", "Currency", "Payment settings"],
                rows,
                empty_message="Add your first business profile."
            ),
            title="Business profiles"
        ),

        active_page="settings",
        page_title="Settings"
    )

# ==================================================
# FORM HELPERS
# ==================================================

def form_field(label, name, placeholder="", field_type="text",
               required=False, value="", step=None):

    return Div(
        Label(label, cls="form-label"),
        Input(
            type=field_type,
            name=name,
            value=value,
            placeholder=placeholder,
            required=required,
            step=step,
            cls="form-input"
        ),
        cls="form-group"
    )


def form_textarea(label, name, placeholder=""):

    return Div(
        Label(label, cls="form-label"),
        Textarea(
            name=name,
            placeholder=placeholder,
            cls="form-textarea"
        ),
        cls="form-group"
    )


def business_options():

    businesses = fetch_all("""
        SELECT id, name
        FROM businesses
        ORDER BY name
    """)

    return [
        Option(business["name"], value=str(business["id"]))
        for business in businesses
    ]


def customer_options():

    customers = fetch_all("""
        SELECT id, name
        FROM customers
        ORDER BY name
    """)

    return [
        Option(customer["name"], value=str(customer["id"]))
        for customer in customers
    ]


# ==================================================
# NEW BUSINESS
# ==================================================

def new_business_page():

    return app_layout(
        page_header(
            "New business",
            "Create a business profile for your workspace."
        ),

        card(
            Form(
                form_field(
                    "Business name",
                    "name",
                    "e.g. Brooklyn Cleaning Co.",
                    required=True
                ),

                form_field(
                    "Email address",
                    "email",
                    "business@example.com",
                    field_type="email"
                ),

                form_field(
                    "Phone number",
                    "phone",
                    "(555) 123-4567"
                ),

                form_textarea(
                    "Business address",
                    "address",
                    "Enter your business address"
                ),

                form_field(
                    "Currency",
                    "currency",
                    value="USD",
                    required=True
                ),

                form_field(
                    "Default tax rate (%)",
                    "tax_rate",
                    value="0",
                    field_type="number",
                    step="0.01"
                ),

                form_textarea(
                    "Payment methods",
                    "payment_methods",
                    "Bank transfer, Cash, Card..."
                ),

                Div(
                    Button(
                        "Create business",
                        type="submit",
                        cls="btn btn-primary"
                    ),
                    A(
                        "Cancel",
                        href="/settings",
                        cls="btn btn-secondary"
                    ),
                    cls="page-actions"
                ),

                method="post",
                action="/settings/businesses/create"
            ),
            title="Business information",
            description="These details will appear on your business documents."
        ),

        active_page="settings",
        page_title="New business"
    )


# ==================================================
# NEW CUSTOMER
# ==================================================

def new_customer_page():

    return app_layout(
        page_header(
            "New customer",
            "Add a customer to your customer directory."
        ),

        card(
            Form(
                form_field(
                    "Customer name",
                    "name",
                    "Full name or company name",
                    required=True
                ),

                form_field(
                    "Email address",
                    "email",
                    "customer@example.com",
                    field_type="email"
                ),

                form_field(
                    "Phone number",
                    "phone",
                    "(555) 123-4567"
                ),

                form_textarea(
                    "Address",
                    "address",
                    "Customer address"
                ),

                form_textarea(
                    "Notes",
                    "notes",
                    "Additional information about this customer"
                ),

                Div(
                    Button(
                        "Create customer",
                        type="submit",
                        cls="btn btn-primary"
                    ),
                    A(
                        "Cancel",
                        href="/customers",
                        cls="btn btn-secondary"
                    ),
                    cls="page-actions"
                ),

                method="post",
                action="/customers/create"
            ),
            title="Customer information"
        ),

        active_page="customers",
        page_title="New customer"
    )


# ==================================================
# NEW SERVICE
# ==================================================

def new_service_page():

    businesses = business_options()

    if not businesses:
        content = Div(
            P("You need to create a business profile before adding services."),
            A(
                button("＋ Create business"),
                href="/settings/businesses/new"
            ),
            cls="empty-state"
        )

    else:
        content = Form(
            Div(
                Label("Business", cls="form-label"),
                Select(
                    Option("Select a business", value=""),
                    *businesses,
                    name="business_id",
                    required=True,
                    cls="form-input"
                ),
                cls="form-group"
            ),

            form_field(
                "Service name",
                "name",
                "e.g. Deep cleaning",
                required=True
            ),

            form_textarea(
                "Description",
                "description",
                "Describe what this service includes"
            ),

            form_field(
                "Price",
                "price",
                "0.00",
                field_type="number",
                required=True,
                step="0.01"
            ),

            Div(
                Button(
                    "Create service",
                    type="submit",
                    cls="btn btn-primary"
                ),
                A(
                    "Cancel",
                    href="/services",
                    cls="btn btn-secondary"
                ),
                cls="page-actions"
            ),

            method="post",
            action="/services/create"
        )

    return app_layout(
        page_header(
            "New service",
            "Create a reusable service and set its price."
        ),

        card(
            content,
            title="Service information"
        ),

        active_page="services",
        page_title="New service"
    )


# ==================================================
# NEW INVOICE / QUOTE
# ==================================================

def new_document_page(doc_type):

    businesses = business_options()
    customers = customer_options()

    title = "New invoice" if doc_type == "invoice" else "New quote"
    endpoint = f"/{doc_type}s/create"
    listing = f"/{doc_type}s"

    if not businesses:
        content = Div(
            P("Create a business profile before creating documents."),
            A(
                button("＋ Create business"),
                href="/settings/businesses/new"
            ),
            cls="empty-state"
        )

    else:
        content = Form(
            Div(
                Label("Business", cls="form-label"),
                Select(
                    Option("Select a business", value=""),
                    *businesses,
                    name="business_id",
                    required=True,
                    cls="form-input"
                ),
                cls="form-group"
            ),

            Div(
                Label("Customer", cls="form-label"),
                Select(
                    Option("No customer selected", value=""),
                    *customers,
                    name="customer_id",
                    cls="form-input"
                ),
                cls="form-group"
            ),

            form_field(
                "Issue date",
                "issue_date",
                field_type="date",
                value=date.today().isoformat(),
                required=True
            ),

            form_field(
                "Due date",
                "due_date",
                field_type="date"
            ),

            Div(
                Button(
                    "Create draft",
                    type="submit",
                    cls="btn btn-primary"
                ),
                A(
                    "Cancel",
                    href=listing,
                    cls="btn btn-secondary"
                ),
                cls="page-actions"
            ),

            method="post",
            action=endpoint
        )

    return app_layout(
        page_header(
            title,
            "Start a new document. You can add services and pricing next."
        ),

        card(
            content,
            title="Document information"
        ),

        active_page=doc_type + "s",
        page_title=title
    )


# ==================================================
# CREATE RECORDS
# ==================================================

def create_business_record(
    name,
    email="",
    phone="",
    address="",
    currency="USD",
    tax_rate=0,
    payment_methods=""
):

    name = name.strip()

    if not name:
        return False

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO businesses (
                name,
                email,
                phone,
                address,
                currency,
                tax_rate,
                payment_methods
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email.strip(),
            phone.strip(),
            address.strip(),
            currency.strip().upper(),
            max(0, float(tax_rate or 0)),
            payment_methods.strip()
        ))

    return True


def create_customer_record(
    name,
    email="",
    phone="",
    address="",
    notes=""
):

    name = name.strip()

    if not name:
        return False

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO customers (
                name,
                email,
                phone,
                address,
                notes
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            email.strip(),
            phone.strip(),
            address.strip(),
            notes.strip()
        ))

    return True


def create_service_record(
    business_id,
    name,
    description="",
    price=0
):

    name = name.strip()

    if not name:
        return False

    with get_connection() as conn:

        business = conn.execute(
            "SELECT id FROM businesses WHERE id = ?",
            (business_id,)
        ).fetchone()

        if not business:
            return False

        conn.execute("""
            INSERT INTO services (
                business_id,
                name,
                description,
                price
            )
            VALUES (?, ?, ?, ?)
        """, (
            business_id,
            name,
            description.strip(),
            max(0, float(price or 0))
        ))

    return True


def create_document_record(
    doc_type,
    business_id,
    customer_id="",
    issue_date="",
    due_date=""
):

    if doc_type not in ("invoice", "quote"):
        return False

    with get_connection() as conn:

        business = conn.execute("""
            SELECT id, currency
            FROM businesses
            WHERE id = ?
        """, (business_id,)).fetchone()

        if not business:
            return False

        if customer_id:
            customer = conn.execute(
                "SELECT id FROM customers WHERE id = ?",
                (customer_id,)
            ).fetchone()

            if not customer:
                return False
        else:
            customer_id = None

        prefix = "INV" if doc_type == "invoice" else "QUO"
        year = date.today().year

        last_id = conn.execute("""
            SELECT COALESCE(MAX(id), 0) + 1
            FROM documents
            WHERE business_id = ? AND doc_type = ?
        """, (business_id, doc_type)).fetchone()[0]

        number = f"{prefix}-{year}-{last_id:05d}"

        conn.execute("""
            INSERT INTO documents (
                business_id,
                customer_id,
                doc_type,
                number,
                status,
                issue_date,
                due_date,
                currency
            )
            VALUES (?, ?, ?, ?, 'draft', ?, ?, ?)
        """, (
            business_id,
            customer_id,
            doc_type,
            number,
            issue_date or date.today().isoformat(),
            due_date,
            business["currency"]
        ))

    return True


# ==================================================
# DOCUMENT EDITOR
# ==================================================

def document_editor_page(document_id):

    document = repo.get_document(document_id)

    if not document:
        return app_layout(
            H2("Document not found"),
            A("Back to invoices", href="/invoices"),
            page_title="Not found"
        )

    business = repo.get_business(document["business_id"])
    customer = (
        repo.get_customer(document["customer_id"])
        if document["customer_id"] else None
    )

    items = repo.get_document_items(document_id)
    services = repo.get_business_services(document["business_id"])
    customers = repo.get_all_customers()

    doc_type = document["doc_type"]
    title = "Invoice" if doc_type == "invoice" else "Quote"
    currency = document["currency"]

    # Existing document items
    item_rows = []

    for item in items:
        item_rows.append(
            Div(
                Form(
                    Div(
                        Input(
                            name="description",
                            value=item["description"],
                            placeholder="Description",
                            cls="form-input"
                        ),
                        Input(
                            name="quantity",
                            type="number",
                            value=item["quantity"],
                            min="0.01",
                            step="0.01",
                            cls="form-input"
                        ),
                        Input(
                            name="unit_price",
                            type="number",
                            value=item["unit_price"],
                            min="0",
                            step="0.01",
                            cls="form-input"
                        ),
                        Button(
                            "Save",
                            type="submit",
                            cls="btn btn-secondary"
                        ),
                        cls="document-item-fields"
                    ),
                    method="post",
                    action=f"/documents/{document_id}/items/{item['id']}/update"
                ),

                Form(
                    Button(
                        "Delete",
                        type="submit",
                        cls="btn btn-danger"
                    ),
                    method="post",
                    action=f"/documents/{document_id}/items/{item['id']}/delete"
                ),

                cls="document-item-row"
            )
        )

    if not item_rows:
        item_rows = [
            P("No items added yet.", cls="empty-state-description")
        ]

    # Existing service options
    service_choices = [
        Option(
            f"{service['name']} — {money(service['price'], currency)}",
            value=str(service["id"])
        )
        for service in services
    ]

    # Customer options
    customer_choices = [
        Option(
            customer_option["name"],
            value=str(customer_option["id"]),
            selected=(
                customer is not None
                and customer_option["id"] == customer["id"]
            )
        )
        for customer_option in customers
    ]

    # Document totals
    subtotal = money(document["subtotal"], currency)
    discount = money(document["discount"], currency)
    tax_amount = money(document["tax_amount"], currency)
    total = money(document["total"], currency)

    return app_layout(

        page_header(
            f"Edit {title.lower()}",
            document["number"],
            actions=[
                A(
                    button("← Back"),
                    href=f"/{'invoices' if doc_type == 'invoice' else 'quotes'}"
                )
            ]
        ),

        # ==========================================
        # DOCUMENT INFORMATION
        # ==========================================

        card(
            Form(
                Div(
                    Label("Customer", cls="form-label"),
                    Select(
                        Option("No customer", value=""),
                        *customer_choices,
                        name="customer_id",
                        cls="form-input"
                    ),
                    cls="form-group"
                ),

                form_field(
                    "Issue date",
                    "issue_date",
                    field_type="date",
                    value=document["issue_date"]
                ),

                form_field(
                    "Due date",
                    "due_date",
                    field_type="date",
                    value=document["due_date"]
                ),

                Div(
                    Button(
                        "Save document details",
                        type="submit",
                        cls="btn btn-primary"
                    ),
                    cls="page-actions"
                ),

                method="post",
                action=f"/documents/{document_id}/update"
            ),
            title="Document details",
            description=(
                business["name"] if business else "Business"
            )
        ),

        # ==========================================
        # ADD EXISTING SERVICE
        # ==========================================

        card(
            Form(
                Div(
                    Label("Select service", cls="form-label"),
                    Select(
                        Option("Choose a service", value=""),
                        *service_choices,
                        name="service_id",
                        required=True,
                        cls="form-input"
                    ),
                    cls="form-group"
                ),

                Button(
                    "＋ Add service",
                    type="submit",
                    cls="btn btn-primary"
                ),

                method="post",
                action=f"/documents/{document_id}/items/add-service"
            ),
            title="Add a service",
            description="Choose a reusable service from your catalogue."
        ),

        # ==========================================
        # ADD CUSTOM ITEM
        # ==========================================

        card(
            Form(
                form_field(
                    "Description",
                    "description",
                    "Describe the work or item",
                    required=True
                ),

                form_field(
                    "Quantity",
                    "quantity",
                    value="1",
                    field_type="number",
                    required=True,
                    step="0.01"
                ),

                form_field(
                    "Unit price",
                    "unit_price",
                    value="0",
                    field_type="number",
                    required=True,
                    step="0.01"
                ),

                Button(
                    "＋ Add custom item",
                    type="submit",
                    cls="btn btn-secondary"
                ),

                method="post",
                action=f"/documents/{document_id}/items/add-custom"
            ),
            title="Custom line item"
        ),

        # ==========================================
        # DOCUMENT ITEMS
        # ==========================================

        card(
            Div(*item_rows, cls="document-items-list"),
            title="Line items",
            description="Edit quantities and prices or remove items."
        ),

        # ==========================================
        # DISCOUNT AND TAX
        # ==========================================

        card(
            Form(
                form_field(
                    "Discount (fixed amount)",
                    "discount",
                    value=str(document["discount"]),
                    field_type="number",
                    step="0.01"
                ),

                form_field(
                    "Tax rate (%)",
                    "tax_rate",
                    value=str(document["tax_rate"]),
                    field_type="number",
                    step="0.01"
                ),

                Button(
                    "Update pricing",
                    type="submit",
                    cls="btn btn-primary"
                ),

                method="post",
                action=f"/documents/{document_id}/pricing"
            ),
            title="Discount and tax"
        ),

        # ==========================================
        # TOTALS
        # ==========================================

        card(
            Div(
                Div(Span("Subtotal"), Strong(subtotal)),
                Div(Span("Discount"), Strong(discount)),
                Div(Span("Tax"), Strong(tax_amount)),
                Div(Span("Total"), Strong(total), cls="document-grand-total"),
                cls="document-totals"
            ),
            title="Document totals"
        ),

        active_page=doc_type + "s",
        page_title=document["number"]
    )


# ==================================================
# BUSINESS PAYMENT SETTINGS
# ==================================================

def payment_methods_page(business_id):

    business = fetch_one("""
        SELECT *
        FROM businesses
        WHERE id = ?
    """, (business_id,))

    if not business:
        return app_layout(
            H2("Business not found"),
            A("Back to settings", href="/settings"),
            page_title="Not found"
        )

    methods = fetch_all("""
        SELECT *
        FROM business_payment_methods
        WHERE business_id = ?
        ORDER BY created_at DESC
    """, (business_id,))

    method_rows = []

    for method in methods:

        details = []

        if method.get("account_name"):
            details.append(
                P(f"Account holder: {method['account_name']}")
            )

        if method.get("bank_name"):
            details.append(
                P(f"Bank: {method['bank_name']}")
            )

        if method.get("account_number"):
            details.append(
                P(f"Account: {method['account_number']}")
            )

        if method.get("routing_number"):
            details.append(
                P(f"Routing: {method['routing_number']}")
            )

        if method.get("sort_code"):
            details.append(
                P(f"Sort code: {method['sort_code']}")
            )

        if method.get("iban"):
            details.append(
                P(f"IBAN: {method['iban']}")
            )

        if method.get("swift_bic"):
            details.append(
                P(f"SWIFT/BIC: {method['swift_bic']}")
            )

        if method.get("payment_handle"):
            details.append(
                P(f"Payment handle: {method['payment_handle']}")
            )

        if method.get("payment_url"):
            details.append(
                P(f"Payment link: {method['payment_url']}")
            )

        if method.get("instructions"):
            details.append(
                P(method["instructions"])
            )

        method_rows.append(
            Div(
                Div(
                    Div(
                        H3(method["display_name"] or method["method_type"].title()),
                        Span(
                            "Active" if method["is_active"] else "Inactive",
                            cls=(
                                "status-badge badge-green"
                                if method["is_active"]
                                else "status-badge badge-gray"
                            )
                        ),
                        cls="payment-method-heading"
                    ),
                    P(
                        method["method_type"].replace("_", " ").title(),
                        cls="form-help"
                    ),
                    *details,
                    cls="payment-method-details"
                ),

                Div(
                    Form(
                        Button(
                            "Deactivate" if method["is_active"] else "Activate",
                            type="submit",
                            cls="btn btn-secondary"
                        ),
                        method="post",
                        action=(
                            f"/settings/businesses/{business_id}"
                            f"/payments/{method['id']}/toggle"
                        )
                    ),

                    Form(
                        Button(
                            "Delete",
                            type="submit",
                            cls="btn btn-danger"
                        ),
                        method="post",
                        action=(
                            f"/settings/businesses/{business_id}"
                            f"/payments/{method['id']}/delete"
                        )
                    ),

                    cls="payment-method-actions"
                ),

                cls="payment-method-card"
            )
        )

    if not method_rows:
        method_rows = [
            empty_state(
                "No payment methods yet",
                "Add a payment method to include receiving details on invoices."
            )
        ]

    return app_layout(
        page_header(
            "Payment methods",
            f"Manage how customers pay {business['name']}.",
            actions=[
                A(
                    button("← Business settings", variant="secondary"),
                    href="/settings"
                )
            ]
        ),

        card(
            Form(
                form_field(
                    "Display name",
                    "display_name",
                    "e.g. Business bank account",
                    required=True
                ),

                Div(
                    Label("Payment type", cls="form-label"),
                    Select(
                        Option("Bank transfer", value="bank_transfer"),
                        Option("Cash", value="cash"),
                        Option("Card", value="card"),
                        Option("PayPal", value="paypal"),
                        Option("Venmo", value="venmo"),
                        Option("Zelle", value="zelle"),
                        Option("Other", value="other"),
                        name="method_type",
                        cls="form-input"
                    ),
                    cls="form-group"
                ),

                form_field(
                    "Account holder / recipient",
                    "account_name",
                    "Business or account holder name"
                ),

                form_field(
                    "Bank name",
                    "bank_name",
                    "Bank name"
                ),

                form_field(
                    "Account number",
                    "account_number",
                    "Receiving account number"
                ),

                form_field(
                    "Routing number",
                    "routing_number",
                    "US routing number"
                ),

                form_field(
                    "Sort code",
                    "sort_code",
                    "UK sort code"
                ),

                form_field(
                    "IBAN",
                    "iban",
                    "International bank account number"
                ),

                form_field(
                    "SWIFT / BIC",
                    "swift_bic",
                    "International bank identifier"
                ),

                form_field(
                    "Payment handle",
                    "payment_handle",
                    "e.g. PayPal email or payment username"
                ),

                form_field(
                    "Payment URL",
                    "payment_url",
                    "https://..."
                ),

                form_textarea(
                    "Payment instructions",
                    "instructions",
                    "Explain how customers should pay. Include payment references or other important instructions."
                ),

                Button(
                    "＋ Add payment method",
                    type="submit",
                    cls="btn btn-primary"
                ),

                method="post",
                action=f"/settings/businesses/{business_id}/payments/create"
            ),
            title="Add payment method",
            description="Enter the receiving details that should appear on invoices."
        ),

        card(
            *method_rows,
            title="Saved payment methods",
            description="These payment methods belong to this business."
        ),

        active_page="settings",
        page_title="Payment methods"
    )

# ==================================================
# ROUTE REGISTRATION
# ==================================================

def register_routes(rt):

    @rt("/")
    def get_dashboard():
        return dashboard_page()

    @rt("/invoices")
    def get_invoices():
        return document_list_page("invoice")

    @rt("/quotes")
    def get_quotes():
        return document_list_page("quote")

    @rt("/customers")
    def get_customers():
        return customers_page()

    @rt("/services")
    def get_services():
        return services_page()

    @rt("/settings")
    def get_settings():
        return settings_page()

    
    # ==========================================
    # NEW BUSINESS
    # ==========================================

    @rt("/settings/businesses/new")
    def get_new_business():
        return new_business_page()

    @rt("/settings/businesses/create", methods=["POST"])
    def post_create_business(
        name: str,
        email: str = "",
        phone: str = "",
        address: str = "",
        currency: str = "USD",
        tax_rate: float = 0,
        payment_methods: str = ""
    ):
        create_business_record(
            name, email, phone, address,
            currency, tax_rate, payment_methods
        )
        return RedirectResponse("/settings", status_code=303)

    # ==========================================
    # NEW CUSTOMER
    # ==========================================

    @rt("/customers/new")
    def get_new_customer():
        return new_customer_page()

    @rt("/customers/create", methods=["POST"])
    def post_create_customer(
        name: str,
        email: str = "",
        phone: str = "",
        address: str = "",
        notes: str = ""
    ):
        create_customer_record(
            name, email, phone, address, notes
        )
        return RedirectResponse("/customers", status_code=303)

    # ==========================================
    # NEW SERVICE
    # ==========================================

    @rt("/services/new")
    def get_new_service():
        return new_service_page()

    @rt("/services/create", methods=["POST"])
    def post_create_service(
        business_id: int,
        name: str,
        description: str = "",
        price: float = 0
    ):
        create_service_record(
            business_id, name, description, price
        )
        return RedirectResponse("/services", status_code=303)

    # ==========================================
    # NEW INVOICE
    # ==========================================

    @rt("/invoices/new")
    def get_new_invoice():
        return new_document_page("invoice")

    @rt("/invoices/create", methods=["POST"])
    def post_create_invoice(
        business_id: int,
        customer_id: str = "",
        issue_date: str = "",
        due_date: str = ""
    ):
        create_document_record(
            "invoice",
            business_id,
            customer_id,
            issue_date,
            due_date
        )
        return RedirectResponse("/invoices", status_code=303)

    # ==========================================
    # NEW QUOTE
    # ==========================================

    @rt("/quotes/new")
    def get_new_quote():
        return new_document_page("quote")

    @rt("/quotes/create", methods=["POST"])
    def post_create_quote(
        business_id: int,
        customer_id: str = "",
        issue_date: str = "",
        due_date: str = ""
    ):
        create_document_record(
            "quote",
            business_id,
            customer_id,
            issue_date,
            due_date
        )
        return RedirectResponse("/quotes", status_code=303)

    
    # ==========================================
    # DOCUMENT EDITOR
    # ==========================================

    @rt("/documents/{document_id}")
    def get_document_editor(document_id: int):
        return document_editor_page(document_id)

    # Update customer and dates
    @rt("/documents/{document_id}/update", methods=["POST"])
    def post_update_document(
        document_id: int,
        customer_id: str = "",
        issue_date: str = "",
        due_date: str = ""
    ):
        document = repo.get_document(document_id)

        if not document:
            return RedirectResponse("/invoices", status_code=303)

        if customer_id:
            customer_id = int(customer_id)
        else:
            customer_id = None

        repo.update_document(
            document_id,
            customer_id=customer_id,
            issue_date=issue_date,
            due_date=due_date
        )

        return RedirectResponse(
            f"/documents/{document_id}",
            status_code=303
        )

    # Add a service from the catalogue
    @rt("/documents/{document_id}/items/add-service", methods=["POST"])
    def post_add_service(
        document_id: int,
        service_id: int
    ):
        document = repo.get_document(document_id)
        service = repo.get_service(service_id)

        if (
            document
            and service
            and service["business_id"] == document["business_id"]
        ):
            document_service.add_item_to_document(
                document_id=document_id,
                description=service["name"],
                quantity=1,
                unit_price=service["price"],
                service_id=service_id
            )

        return RedirectResponse(
            f"/documents/{document_id}",
            status_code=303
        )

    # Add a custom item
    @rt("/documents/{document_id}/items/add-custom", methods=["POST"])
    def post_add_custom_item(
        document_id: int,
        description: str,
        quantity: float = 1,
        unit_price: float = 0
    ):
        document = repo.get_document(document_id)

        if document:
            document_service.add_item_to_document(
                document_id,
                description,
                quantity,
                unit_price
            )

        return RedirectResponse(
            f"/documents/{document_id}",
            status_code=303
        )

    # Edit an existing item
    @rt("/documents/{document_id}/items/{item_id}/update", methods=["POST"])
    def post_update_item(
        document_id: int,
        item_id: int,
        description: str,
        quantity: float,
        unit_price: float
    ):
        item = next(
            (
                item for item in repo.get_document_items(document_id)
                if item["id"] == item_id
            ),
            None
        )

        if item:
            document_service.edit_document_item(
                item_id,
                description=description,
                quantity=quantity,
                unit_price=unit_price
            )

        return RedirectResponse(
            f"/documents/{document_id}",
            status_code=303
        )

    # Delete an item
    @rt("/documents/{document_id}/items/{item_id}/delete", methods=["POST"])
    def post_delete_item(document_id: int, item_id: int):

        item = next(
            (
                item for item in repo.get_document_items(document_id)
                if item["id"] == item_id
            ),
            None
        )

        if item:
            document_service.remove_document_item(item_id)

        return RedirectResponse(
            f"/documents/{document_id}",
            status_code=303
        )

    # Update discount and tax
    @rt("/documents/{document_id}/pricing", methods=["POST"])
    def post_update_pricing(
        document_id: int,
        discount: float = 0,
        tax_rate: float = 0
    ):
        document = repo.get_document(document_id)

        if document:
            document_service.update_document_pricing(
                document_id,
                discount=discount,
                tax_rate=tax_rate
            )

        return RedirectResponse(
            f"/documents/{document_id}",
            status_code=303
        )

    
    # ==========================================
    # BUSINESS PAYMENT METHODS
    # ==========================================

    @rt("/settings/businesses/{business_id}/payments")
    def get_business_payments(business_id: int):
        return payment_methods_page(business_id)

    @rt(
        "/settings/businesses/{business_id}/payments/create",
        methods=["POST"]
    )
    def post_create_payment_method(
        business_id: int,
        display_name: str,
        method_type: str,
        account_name: str = "",
        bank_name: str = "",
        account_number: str = "",
        routing_number: str = "",
        sort_code: str = "",
        iban: str = "",
        swift_bic: str = "",
        payment_handle: str = "",
        payment_url: str = "",
        instructions: str = ""
    ):

        allowed_types = {
            "bank_transfer", "cash", "card",
            "paypal", "venmo", "zelle", "other"
        }

        business = fetch_one(
            "SELECT id FROM businesses WHERE id = ?",
            (business_id,)
        )

        if business and method_type in allowed_types and display_name.strip():

            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO business_payment_methods (
                        business_id,
                        method_type,
                        display_name,
                        account_name,
                        bank_name,
                        account_number,
                        routing_number,
                        sort_code,
                        iban,
                        swift_bic,
                        payment_handle,
                        payment_url,
                        instructions
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    business_id,
                    method_type,
                    display_name.strip(),
                    account_name.strip(),
                    bank_name.strip(),
                    account_number.strip(),
                    routing_number.strip(),
                    sort_code.strip(),
                    iban.strip(),
                    swift_bic.strip(),
                    payment_handle.strip(),
                    payment_url.strip(),
                    instructions.strip()
                ))

        return RedirectResponse(
            f"/settings/businesses/{business_id}/payments",
            status_code=303
        )

    # Activate / deactivate a payment method
    @rt(
        "/settings/businesses/{business_id}/payments/{method_id}/toggle",
        methods=["POST"]
    )
    def post_toggle_payment_method(
        business_id: int,
        method_id: int
    ):

        with get_connection() as conn:

            method = conn.execute("""
                SELECT id, is_active
                FROM business_payment_methods
                WHERE id = ? AND business_id = ?
            """, (method_id, business_id)).fetchone()

            if method:
                new_status = 0 if method["is_active"] else 1

                conn.execute("""
                    UPDATE business_payment_methods
                    SET is_active = ?
                    WHERE id = ? AND business_id = ?
                """, (new_status, method_id, business_id))

        return RedirectResponse(
            f"/settings/businesses/{business_id}/payments",
            status_code=303
        )

    # Delete a payment method
    @rt(
        "/settings/businesses/{business_id}/payments/{method_id}/delete",
        methods=["POST"]
    )
    def post_delete_payment_method(
        business_id: int,
        method_id: int
    ):

        with get_connection() as conn:
            conn.execute("""
                DELETE FROM business_payment_methods
                WHERE id = ? AND business_id = ?
            """, (method_id, business_id))

        return RedirectResponse(
            f"/settings/businesses/{business_id}/payments",
            status_code=303
        )



