
from pathlib import Path

# Get the main project directory.
BASE_DIR = Path(__file__).resolve().parent

# Application folders.
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

# Database location.
DB_PATH = DATA_DIR / "servicedesk.sqlite3"

# Application settings.
APP_NAME = "ServiceDesk"

# Default currency.
DEFAULT_CURRENCY = "USD"

# Default timezone.
DEFAULT_TIMEZONE = "America/New_York"
