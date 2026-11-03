import requests
from datetime import datetime, timezone
from config import Config

def normalize_fields(lead):
    result = {}

    for field in lead.get("field_data", []):
        name = field.get("name", "").strip().lower()
        values = field.get("values", [])

        if values:
            result[name] = str(values[0]).strip()

    return result

def get_field(data, *names):
    for name in names:
        value = data.get(name.lower())

        if value:
            return str(value).strip()

    return ""

def find_field_by_keyword(data, *keywords):
    for name, value in data.items():
        if not value:
            continue

        if any(keyword in name for keyword in keywords):
            return str(value).strip()

    return ""

def extract_fields(lead):
    return normalize_fields(lead)

def get_lead_name(data):
    name = get_field(
        data,
        "full_name",
        "name",
        "укажите_ваше_имя_и_фамилию:"
    )

    if name:
        return name

    name = find_field_by_keyword(
        data,
        "укажите_ваше_имя",
        "full_name"
    )

    if name:
        return name

    first_name = get_field(data, "first_name")
    last_name = get_field(data, "last_name")

    return f"{first_name} {last_name}".strip()

def get_lead_phone(data):
    phone = get_field(
        data,
        "phone_number",
        "phone",
        "mobile_number"
    )

    if phone:
        return phone

    return find_field_by_keyword(
        data,
        "телефон",
        "phone"
    )

def get_lead_email(data):
    return get_field(
        data,
        "email",
        "e_mail"
    )


def format_lead_answers(data):
    lines = []

    excluded_fields = {
        "full_name",
        "name",
        "first_name",
        "last_name",
        "phone_number",
        "phone",
        "mobile_number",
        "email",
        "e_mail",
        "укажите_ваше_имя_и_фамилию:",
        "укажите_ваш_действующий_номер_телефона_для_связи:"
    }

    for field_name, value in data.items():
        if field_name in excluded_fields:
            continue

        if not value:
            continue

        readable_name = field_name.replace("_", " ").strip()

        lines.append(
            f"{readable_name}: {value}"
        )

    return "\n".join(lines)


def create_crm_payload(lead, page_id=None):
    data = extract_fields(lead)

    full_name = get_lead_name(data)
    phone = get_lead_phone(data)
    email = get_lead_email(data)

    city = get_field(data, "city")

    answers = format_lead_answers(data)

    created_time = lead.get("created_time")

    if created_time:
        date = datetime.strptime(
            created_time,
            "%Y-%m-%dT%H:%M:%S%z"
        ).strftime("%Y-%m-%d %H:%M:%S")
    else:
        date = datetime.now(timezone.utc)

    message = "Instagram reklamasidan yangi murojaat."

    if answers:
        message += "\n\nLead form javoblari:\n" + answers

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
        "MesajNotu": message,
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

def send_to_crm(payload):
    if not Config.CRM_API_URL:
        raise ValueError("CRM_API_URL is not configured")

    if not Config.CRM_API_KEY:
        raise ValueError("CRM_API_KEY is not configured")

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

    if not response.ok:
        raise Exception(
            f"CRM HTTP error: {response.status_code} "
            f"{response.text[:1000]}"
        )

    try:
        result = response.json()
    except ValueError:
        raise Exception(
            f"CRM returned invalid JSON: {response.text[:1000]}"
        )

    if isinstance(result, list):
        result = result[0] if result else {}

    if not isinstance(result, dict) or result.get("Durum") != 1:
        raise Exception(f"CRM rejected lead: {result}")

    return result
