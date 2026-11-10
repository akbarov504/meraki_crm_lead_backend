
import re
import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

def extract_phone_number(message_text):
    if not message_text:
        return None

    candidates = re.findall(
        r"(?<!\d)\+?\d[\d\s().-]{6,}\d(?!\d)",
        message_text
    )

    for candidate in candidates:
        digits = re.sub(r"\D", "", candidate)

        if len(digits) == 9:
            return "+998" + digits

        if len(digits) == 12 and digits.startswith("998"):
            return "+" + digits

        if candidate.strip().startswith("+") and 10 <= len(digits) <= 15:
            return "+" + digits

    return None

def get_instagram_username(igsid):
    if not Config.META_PAGE_ACCESS_TOKEN:
        logger.error("META_PAGE_ACCESS_TOKEN is not configured")
        return f"Instagram user {igsid}"

    url = (f"https://graph.facebook.com/" f"{Config.META_GRAPH_API_VERSION}/{igsid}")

    params = {
        "fields": "username,name",
        "access_token": Config.META_PAGE_ACCESS_TOKEN
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if not response.ok:
            logger.error("Instagram profile API error: %s %s", response.status_code, response.text[:500])
            return f"Instagram user {igsid}"

        data = response.json()
        username = data.get("username")
        if username:
            return username.lstrip("@")

        name = data.get("name")
        if name:
            return name

    except requests.RequestException:
        logger.exception("Instagram username olishda xatolik. IGSID: %s", igsid)

    return f"Instagram user {igsid}"
