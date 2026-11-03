import requests
from config import Config
from datetime import datetime, timezone

def get_field(data, *names):
    for name in names:
        value = data.get(name.lower())

        if value:
            return str(value).strip()

    return ""

def create_crm_payload(lead, page_id=None):
    data = extract_fields(lead)

    full_name = get_field(
        data,
        "full_name",
        "name"
    )

    if not full_name:
        first_name = get_field(data, "first_name")
        last_name = get_field(data, "last_name")
        full_name = f"{first_name} {last_name}".strip()

    phone = get_field(
        data,
        "phone_number",
        "phone",
        "mobile_number"
    )

    email = get_field(
        data,
        "email",
        "e_mail"
    )

    city = get_field(data, "city")
    message = get_field(
        data,
        "message",
        "your_message",
        "description"
    )

    created_time = lead.get("created_time")

    if created_time:
        date = datetime.fromisoformat(
            created_time.replace("Z", "+00:00")
        ).strftime("%Y-%m-%d %H:%M:%S")
    else:
        date = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    return {
        "MusteriAdiSoyadi": full_name,
        "PersonelID": 0,
        "Email": email,
        "Telefon": phone,
        "IletisimAdresi": "",
        "IletisimUlkeID": 0,
        "IletisimSehir": city,
        "IletisimIlce": "",
        "IletisimSemt": "",
        "MesajNotu": message or "Instagram reklamidan yangi murojaat.",
        "Tarih": date,
        "MailIstiyorMu": bool(email),
        "MusteriKaynagiID": 16,
        "InfoUrl": "",
        "WebSitesi": "",
        "MusteriID": 0,
        "MusteriIletisimID": 0,
        "BulunanMusteriID": 0,
        "NetIp": "",
        "InfoFormGelisYeri": "Instagram",
        "InfoFormGelisYeri2": "Meta Lead Ads",
        "DigerYazilimNo": str(lead.get("id", "")),
        "UtmCode": "",
        "KarakterAlan1": str(lead.get("form_id", "")),
        "KarakterAlan2": str(lead.get("ad_id", "")),
        "KarakterAlan3": str(page_id or ""),
        "KarakterAlan4": "",
        "KarakterAlan5": "",
        "InfoFormTalepID": 1,
        "EmailOnay": True,
        "SmsOnay": False,
        "TelOnay": False,
        "InfoFormGelisYeri3": "",
        "InfoFormGelisYeri4": "",
        "InfoFormGelisYeri5": ""
    }

def extract_fields(lead):
    result = {}

    for field in lead.get("field_data", []):
        name = field.get("name", "").lower()
        values = field.get("values", [])

        if values:
            result[name] = values[0]

    return result

def send_to_crm(payload):
    headers = {
        Config.CRM_API_KEY_HEADER: Config.CRM_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(
        Config.CRM_API_URL,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    if isinstance(result, list):
        result = result[0] if result else {}

    if not isinstance(result, dict) or result.get("Durum") != 1:
        raise Exception(f"CRM rejected lead: {result}")

    return result
