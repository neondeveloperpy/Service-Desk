# ServiceDesk — FastHTML Quote & Invoice App

A modular starter application for small service businesses such as cleaning
companies, contractors, and independent service providers.

## Features

- Customer directory
- Quote creation with up to eight line items
- Invoice creation with due dates
- Automatic subtotal, tax, and total calculations
- Downloadable PDF quotes and invoices
- Paid / unpaid invoice tracking
- SQLite database
- Custom responsive CSS stylesheet

## Project structure

```text
servicedesk/
├── app.py                  # Application entry point
├── config.py               # App settings
├── routes.py               # URL routes and request handling
├── requirements.txt
├── database/
│   ├── __init__.py
│   ├── db.py               # SQLite connection and table creation
│   └── repositories.py     # SQL queries and persistence
├── services/
│   ├── __init__.py
│   ├── documents.py        # Validation and quote/invoice calculations
│   └── pdf.py              # PDF generation
├── ui/
│   ├── __init__.py
│   ├── layout.py           # Shared page layout and navigation
│   └── components.py       # Reusable UI elements
├── static/
│   └── css/
│       └── styles.css      # All custom styling
└── data/                   # SQLite database is created here
```

## How the architecture works

A browser request enters through a route in `routes.py`. The route calls a
service when it needs business logic. The service uses the repository layer
to read or write data. The route then returns a page built from reusable
components in `ui/`.

```text
Browser
   |
   v
routes.py       Handles URLs and form submissions
   |
   v
services/       Validates input and calculates totals
   |
   v
database/       Reads and writes SQLite records

routes.py ---> ui/       Builds the HTML pages
routes.py ---> services/pdf.py   Generates PDF downloads
```

This separation means you can update the PDF layout without changing database
queries, or redesign the CSS without rewriting the business logic.

## Run locally

Python 3.10+ is recommended.

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the app

```bash
python app.py
```

Open http://localhost:5001

## Configuration

Change the defaults in `config.py`, or set environment variables:

- `DATABASE_PATH` — location of the SQLite database file
- `CURRENCY_SYMBOL` — currency symbol shown in the UI and PDFs

For example, on macOS/Linux:

```bash
CURRENCY_SYMBOL="$" python app.py
```

## Where to make common changes

| I want to change... | Edit this file |
|---|---|
| Colors, spacing, fonts, responsive design | `static/css/styles.css` |
| Navigation and shared page wrapper | `ui/layout.py` |
| Reusable tables, buttons, form fields | `ui/components.py` |
| URLs and form submission behavior | `routes.py` |
| Tax and total calculations | `services/documents.py` |
| PDF appearance | `services/pdf.py` |
| Database tables | `database/db.py` |
| SQL queries | `database/repositories.py` |
| Currency and app settings | `config.py` |

## Current MVP limitations

- One local business / one local database.
- No login or user accounts yet.
- No editing or deleting records yet.
- Quote-to-invoice conversion is not implemented yet.
- Business name and logo on PDFs are placeholders.
- No email sending or online payments.
- The app should be secured before being exposed publicly.

## Before production

Add authentication and authorization, CSRF protection, stronger form validation,
database backups, secure configuration, logging, and tests. If multiple businesses
will use the hosted app, add business ownership to the data model and ensure every
query is scoped to the signed-in business.
