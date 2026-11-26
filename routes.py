
from fasthtml.common import *

from database.db import get_connection
from ui.layout import app_layout
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

    rows = [
        [
            get_value(business, "name"),
            get_value(business, "email"),
            get_value(business, "phone"),
            get_value(business, "currency"),
        ]
        for business in businesses
    ]

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
                ["Business", "Email", "Phone", "Currency"],
                rows,
                empty_message="Add your first business profile."
            ),
            title="Business profiles"
        ),

        active_page="settings",
        page_title="Settings"
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
