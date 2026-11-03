import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
    META_APP_SECRET = os.getenv("META_APP_SECRET")
    META_PAGE_ACCESS_TOKEN = os.getenv("META_PAGE_ACCESS_TOKEN")
    META_GRAPH_API_VERSION = os.getenv(
        "META_GRAPH_API_VERSION",
        "v23.0"
    )

    CRM_API_URL = os.getenv("CRM_API_URL")
    CRM_API_KEY = os.getenv("CRM_API_KEY")
    CRM_API_KEY_HEADER = os.getenv("CRM_API_KEY_HEADER", "key")
