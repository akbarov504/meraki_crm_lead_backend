import requests
from config import Config

def get_lead_details(lead_id):
    if not Config.META_PAGE_ACCESS_TOKEN:
        raise ValueError("META_PAGE_ACCESS_TOKEN is not configured")

    url = (
        f"https://graph.facebook.com/"
        f"{Config.META_GRAPH_API_VERSION}/{lead_id}"
    )

    params = {
        "fields": "id,created_time,field_data,form_id,ad_id",
        "access_token": Config.META_PAGE_ACCESS_TOKEN
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    if not response.ok:
        raise Exception(
            f"Meta API error: {response.status_code} "
            f"{response.text[:1000]}"
        )

    data = response.json()

    if not data.get("id"):
        raise ValueError(
            f"Meta returned invalid lead data: {data}"
        )

    return data

def extract_lead_data(lead):
    result = {}

    for field in lead.get("field_data", []):
        name = field.get("name", "").strip().lower()
        values = field.get("values", [])

        if values:
            result[name] = values[0]

    return result
