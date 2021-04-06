from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEBUG = False

DEV_USER_ID = 367833544

if DEBUG:
    TOKEN = "5b3bbf7ba70a127726b59080f1fc0449083194da11f750b8dbc997aeece0f23fcd99eedea421d546e94fe"
else:
    TOKEN = "5367dc444aed6e1e5609f94f430cf860d59d9f303bb61c28da2e551c6961ff0cd0875f8bd4ef2c6b25d45"
