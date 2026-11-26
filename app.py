
from fasthtml.common import *

from config import APP_NAME
from database.db import init_db
from routes import register_routes


# Create the FastHTML application.
app, rt = fast_app(
    title=APP_NAME,
    hdrs=(
        Link(
            rel="stylesheet",
            href="/static/css/styles.css"
        ),
        Script(src="/static/js/theme.js"),
    )
)


# Initialize the database tables.
init_db()


# Register application routes.
register_routes(rt)


# Start the application.
serve()
