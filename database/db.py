
import sqlite3

from config import DB_PATH, DATA_DIR


def get_connection():
    """
    Create and return a connection to our SQLite database.

    This function also:
    - Creates the data folder if it doesn't exist.
    - Allows us to access database columns by name.
    - Enables foreign key relationships.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    # Allows us to use row["column_name"] instead of row[0].
    connection.row_factory = sqlite3.Row

    # Enable foreign key relationships.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db():
    """
    Create all database tables if they don't already exist.

    Running this function multiple times will not delete
    existing information.
    """

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
        # Each service belongs to a business.
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
        #
        # Both use the same table.
        # doc_type determines whether it's an
        # invoice or a quote.
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
        # Individual products or services inside
        # invoices and quotes.
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
        # DOCUMENT NOTES AND COMMENTS
        # Allows multiple comments per document.
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
        # We store the file location in the database,
        # not the actual file contents.
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
        # INDEXES
        # Help speed up common database searches.
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

    print("ServiceDesk database initialized successfully.")
