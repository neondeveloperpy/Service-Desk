
from fasthtml.common import *


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

def nav_link(label, href, icon, active=False):
    return A(
        Span(icon, cls="nav-icon"),
        Span(label, cls="nav-label"),
        href=href,
        cls="nav-link active" if active else "nav-link"
    )


def sidebar(active_page="dashboard"):
    navigation = [
        ("dashboard", "Dashboard", "/", "▦"),
        ("invoices", "Invoices", "/invoices", "▤"),
        ("quotes", "Quotes", "/quotes", "▧"),
        ("customers", "Customers", "/customers", "♙"),
        ("services", "Services", "/services", "◇"),
    ]

    return Aside(
        Div(
            Div("S", cls="logo-icon"),
            Div(
                H2("ServiceDesk"),
                P("Business management"),
                cls="logo-text"
            ),
            cls="sidebar-brand"
        ),

        Div("WORKSPACE", cls="sidebar-section-label"),

        Nav(
            *[
                nav_link(
                    label,
                    href,
                    icon,
                    active=(active_page == page)
                )
                for page, label, href, icon in navigation
            ],
            cls="sidebar-nav"
        ),

        Div(cls="sidebar-spacer"),

        Div("PREFERENCES", cls="sidebar-section-label"),

        Nav(
            nav_link(
                "Settings",
                "/settings",
                "⚙",
                active=(active_page == "settings")
            ),
            cls="sidebar-nav"
        ),

        Div(
            Div("SD", cls="profile-avatar"),
            Div(
                Strong("My Business"),
                Small("Business account"),
                cls="profile-details"
            ),
            cls="sidebar-profile"
        ),

        cls="sidebar"
    )


# --------------------------------------------------
# TOP BAR
# --------------------------------------------------

def topbar(page_title="Dashboard"):
    return Header(
        Div(
            H2(page_title, cls="topbar-title"),
            cls="topbar-heading"
        ),

        Div(
            Button(
                "☼",
                type="button",
                cls="theme-toggle",
                title="Toggle theme"
            ),
            Div(
                "SD",
                cls="topbar-avatar"
            ),
            cls="topbar-actions"
        ),

        cls="topbar"
    )


# --------------------------------------------------
# MAIN APPLICATION LAYOUT
# --------------------------------------------------

def app_layout(
    *content,
    active_page="dashboard",
    page_title="Dashboard"
):
    """
    Wraps a page in the main ServiceDesk layout.

    Example:
    return app_layout(
        H1("Dashboard"),
        active_page="dashboard",
        page_title="Dashboard"
    )
    """

    return Div(
        sidebar(active_page),

        Div(
            topbar(page_title),

            Main(
                *content,
                cls="main-content"
            ),

            cls="main-panel"
        ),

        cls="app-shell"
    )
