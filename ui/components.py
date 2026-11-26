
from fasthtml.common import *


# --------------------------------------------------
# BUTTONS
# --------------------------------------------------

def button(
    text,
    variant="primary",
    type="button",
    icon=None,
    **kwargs
):
    """
    Reusable button.

    Variants:
    - primary
    - secondary
    - danger
    - ghost
    """

    content = []

    if icon:
        content.append(
            Span(icon, cls="button-icon")
        )

    content.append(text)

    return Button(
        *content,
        type=type,
        cls=f"btn btn-{variant}",
        **kwargs
    )


# --------------------------------------------------
# STATUS BADGES
# --------------------------------------------------

def status_badge(status):
    """
    Displays a colored badge based on document status.
    """

    status_classes = {
        "draft": "badge-gray",
        "sent": "badge-blue",
        "paid": "badge-green",
        "overdue": "badge-red",
        "cancelled": "badge-gray",
        "accepted": "badge-green",
        "rejected": "badge-red",
        "pending": "badge-yellow",
    }

    status = str(status).lower()

    badge_class = status_classes.get(
        status,
        "badge-gray"
    )

    return Span(
        status.capitalize(),
        cls=f"status-badge {badge_class}"
    )


# --------------------------------------------------
# CARDS
# --------------------------------------------------

def card(*children, title=None, description=None, cls=""):
    """
    General-purpose content card.
    """

    header = []

    if title or description:
        header.append(
            Div(
                H3(title, cls="card-title") if title else None,
                P(description, cls="card-description")
                if description else None,
                cls="card-header"
            )
        )

    return Div(
        *header,
        Div(*children, cls="card-content"),
        cls=f"card {cls}".strip()
    )


# --------------------------------------------------
# STATISTIC CARDS
# --------------------------------------------------

def stat_card(
    title,
    value,
    description=None,
    icon=None,
    trend=None,
    trend_type="neutral"
):
    """
    Dashboard statistic card.

    Example:
    stat_card(
        "Total Revenue",
        "$4,500",
        description="Compared to last month",
        trend="+12%"
    )
    """

    icon_element = None

    if icon:
        icon_element = Div(
            icon,
            cls="stat-icon"
        )

    trend_element = None

    if trend:
        trend_element = Span(
            trend,
            cls=f"stat-trend trend-{trend_type}"
        )

    return Div(
        Div(
            Div(
                Span(title, cls="stat-title"),
                H2(value, cls="stat-value"),
                cls="stat-main"
            ),
            icon_element,
            cls="stat-top"
        ),
        Div(
            P(description, cls="stat-description")
            if description else None,
            trend_element,
            cls="stat-bottom"
        ),
        cls="stat-card"
    )


# --------------------------------------------------
# PAGE HEADERS
# --------------------------------------------------

def page_header(
    title,
    description=None,
    actions=None
):
    """
    Standard page heading with optional action buttons.

    Example:
    page_header(
        "Invoices",
        "Manage your invoices",
        actions=button("New invoice")
    )
    """

    return Div(
        Div(
            H1(title, cls="page-title"),
            P(description, cls="page-description")
            if description else None,
            cls="page-heading"
        ),
        Div(*actions, cls="page-actions")
        if actions else None,
        cls="page-header"
    )


# --------------------------------------------------
# EMPTY STATES
# --------------------------------------------------

def empty_state(
    title,
    description,
    action=None,
    icon="📄"
):
    """
    Shown when a list or section has no content.
    """

    return Div(
        Div(icon, cls="empty-state-icon"),
        H3(title, cls="empty-state-title"),
        P(description, cls="empty-state-description"),
        Div(action, cls="empty-state-action")
        if action else None,
        cls="empty-state"
    )


# --------------------------------------------------
# FORM FIELDS
# --------------------------------------------------

def form_field(
    label,
    name,
    input_type="text",
    placeholder="",
    value="",
    required=False,
    help_text=None
):
    """
    Reusable text, email, number, and date input.

    Example:
    form_field(
        "Customer name",
        "name",
        placeholder="Enter customer name",
        required=True
    )
    """

    return Div(
        Label(
            label,
            For=name,
            cls="form-label"
        ),
        Input(
            type=input_type,
            name=name,
            id=name,
            placeholder=placeholder,
            value=value,
            required=required,
            cls="form-input"
        ),
        P(help_text, cls="form-help")
        if help_text else None,
        cls="form-group"
    )


def textarea_field(
    label,
    name,
    placeholder="",
    value="",
    rows=4,
    required=False,
    help_text=None
):
    """
    Reusable textarea field.
    """

    return Div(
        Label(
            label,
            For=name,
            cls="form-label"
        ),
        Textarea(
            value,
            name=name,
            id=name,
            placeholder=placeholder,
            rows=rows,
            required=required,
            cls="form-input form-textarea"
        ),
        P(help_text, cls="form-help")
        if help_text else None,
        cls="form-group"
    )


# --------------------------------------------------
# SEARCH INPUT
# --------------------------------------------------

def search_input(
    name="search",
    placeholder="Search...",
    value=""
):
    """
    Reusable search input.
    """

    return Div(
        Span("⌕", cls="search-icon"),
        Input(
            type="search",
            name=name,
            placeholder=placeholder,
            value=value,
            cls="search-field"
        ),
        cls="search-box"
    )


# --------------------------------------------------
# TABLE
# --------------------------------------------------

def data_table(headers, rows, empty_message="No records found"):
    """
    Basic reusable table.

    headers = ["Invoice", "Customer", "Amount", "Status"]

    rows = [
        ["INV-001", "John Smith", "$250", status_badge("paid")],
        ...
    ]
    """

    if not rows:
        return Div(
            P(empty_message, cls="table-empty"),
            cls="table-empty-container"
        )

    return Div(
        Table(
            Thead(
                Tr(
                    *[
                        Th(header)
                        for header in headers
                    ]
                )
            ),
            Tbody(
                *[
                    Tr(
                        *[
                            Td(cell)
                            for cell in row
                        ]
                    )
                    for row in rows
                ]
            ),
            cls="data-table"
        ),
        cls="table-container"
    )


# --------------------------------------------------
# DIVIDERS
# --------------------------------------------------

def section_divider():
    return Hr(cls="section-divider")
