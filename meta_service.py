import requests
from config import Config

def get_lead_details(lead_id):
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

    response.raise_for_status()
    return response.json()

def extract_lead_data(lead):
    field_data = lead.get("field_data", [])

    data = {}

    for field in field_data:
        name = field.get("name", "").lower()
        values = field.get("values", [])

        if values:
            data[name] = values[0]

    return data
