
import sqlite3

from config import DB_PATH, DATA_DIR


def get_connection():
    """
    Create a database connection.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def add_column_if_missing(conn, table, column, definition):
    """
    Safely add a column to an existing table.

    This allows us to improve the database without
    deleting existing records.
    """

    existing_columns = {
        row["name"]
        for row in conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }

    if column not in existing_columns:
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def init_db():

    with get_connection() as conn:

        # ==========================================
        # BUSINESSES
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS businesses (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                address TEXT DEFAULT '',

                logo_path TEXT DEFAULT '',

                currency TEXT DEFAULT 'USD',

                tax_rate REAL DEFAULT 0,

                payment_methods TEXT DEFAULT '',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==========================================
        # CUSTOMERS
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                address TEXT DEFAULT '',

                notes TEXT DEFAULT '',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ==========================================
        # SERVICES
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS services (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                business_id INTEGER NOT NULL,

                name TEXT NOT NULL,
                description TEXT DEFAULT '',

                price REAL NOT NULL DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (business_id)
                    REFERENCES businesses(id)
                    ON DELETE CASCADE
            )
        """)

        # ==========================================
        # INVOICES AND QUOTES
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                business_id INTEGER NOT NULL,
                customer_id INTEGER,

                doc_type TEXT NOT NULL
                    CHECK(doc_type IN ('invoice', 'quote')),

                number TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'draft',

                issue_date TEXT DEFAULT '',
                due_date TEXT DEFAULT '',

                currency TEXT DEFAULT 'USD',

                subtotal REAL DEFAULT 0,
                discount REAL DEFAULT 0,

                tax_rate REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,

                total REAL DEFAULT 0,

                notes TEXT DEFAULT '',
                payment_terms TEXT DEFAULT '',

                email_sent_at TEXT DEFAULT '',
                paid_at TEXT DEFAULT '',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(business_id, number),

                FOREIGN KEY (business_id)
                    REFERENCES businesses(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (customer_id)
                    REFERENCES customers(id)
                    ON DELETE SET NULL
            )
        """)

        # ==========================================
        # DOCUMENT ITEMS
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_items (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                document_id INTEGER NOT NULL,
                service_id INTEGER,

                description TEXT NOT NULL,

                quantity REAL NOT NULL DEFAULT 1,
                unit_price REAL NOT NULL DEFAULT 0,
                line_total REAL NOT NULL DEFAULT 0,

                FOREIGN KEY (document_id)
                    REFERENCES documents(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (service_id)
                    REFERENCES services(id)
                    ON DELETE SET NULL
            )
        """)

        # ==========================================
        # DOCUMENT NOTES
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_notes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                document_id INTEGER NOT NULL,
                body TEXT NOT NULL,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (document_id)
                    REFERENCES documents(id)
                    ON DELETE CASCADE
            )
        """)

        # ==========================================
        # ATTACHMENTS
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS attachments (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                document_id INTEGER NOT NULL,

                filename TEXT NOT NULL,
                stored_path TEXT NOT NULL,

                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (document_id)
                    REFERENCES documents(id)
                    ON DELETE CASCADE
            )
        """)

        # ==========================================
        # BUSINESS PAYMENT METHODS
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS business_payment_methods (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                business_id INTEGER NOT NULL,

                method_type TEXT NOT NULL,
                display_name TEXT DEFAULT '',

                account_name TEXT DEFAULT '',
                bank_name TEXT DEFAULT '',

                account_number TEXT DEFAULT '',
                routing_number TEXT DEFAULT '',
                sort_code TEXT DEFAULT '',

                iban TEXT DEFAULT '',
                swift_bic TEXT DEFAULT '',

                payment_handle TEXT DEFAULT '',
                payment_url TEXT DEFAULT '',

                instructions TEXT DEFAULT '',

                is_active INTEGER DEFAULT 1,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (business_id)
                    REFERENCES businesses(id)
                    ON DELETE CASCADE
            )
        """)

        # ==========================================
        # DOCUMENT PAYMENT METHOD SNAPSHOTS
        #
        # Copies payment details onto an invoice.
        # Later changes to business payment settings
        # will not alter an existing invoice.
        # ==========================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_payment_methods (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                document_id INTEGER NOT NULL,

                business_payment_method_id INTEGER,

                method_type TEXT NOT NULL,
                display_name TEXT DEFAULT '',

                account_name TEXT DEFAULT '',
                bank_name TEXT DEFAULT '',

                account_number TEXT DEFAULT '',
                routing_number TEXT DEFAULT '',
                sort_code TEXT DEFAULT '',

                iban TEXT DEFAULT '',
                swift_bic TEXT DEFAULT '',

                payment_handle TEXT DEFAULT '',
                payment_url TEXT DEFAULT '',

                instructions TEXT DEFAULT '',

                display_order INTEGER DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (document_id)
                    REFERENCES documents(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (business_payment_method_id)
                    REFERENCES business_payment_methods(id)
                    ON DELETE SET NULL
            )
        """)

        # ==========================================
        # DATABASE MIGRATIONS
        #
        # These also run against existing databases.
        # ==========================================

        # Quote-specific information
        add_column_if_missing(
            conn, "documents", "valid_until", "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn, "documents", "assumptions", "TEXT DEFAULT ''"
        )

        add_column_if_missing(
            conn, "documents", "exclusions", "TEXT DEFAULT ''"
        )

        # Link an invoice to its original quote
        add_column_if_missing(
            conn,
            "documents",
            "source_quote_id",
            "INTEGER REFERENCES documents(id) ON DELETE SET NULL"
        )

        # ==========================================
        # INDEXES
        # ==========================================

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_business
            ON documents(business_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_customer
            ON documents(customer_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_type_status
            ON documents(doc_type, status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_source_quote
            ON documents(source_quote_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_services_business
            ON services(business_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_items_document
            ON document_items(document_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_document
            ON document_notes(document_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_attachments_document
            ON attachments(document_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_payment_methods_business
            ON business_payment_methods(business_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_payment_methods
            ON document_payment_methods(document_id)
        """)

    print("ServiceDesk database initialized successfully.")
