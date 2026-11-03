import hmac
import hashlib
import logging
from config import Config
from flask import Flask, request, jsonify
from meta_service import get_lead_details
from crm_service import create_crm_payload, send_to_crm
from database import init_db, is_processed, save_lead_status

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

logger = logging.getLogger(__name__)
init_db()

def verify_meta_signature(raw_body, signature):
    if not Config.META_APP_SECRET:
        return False

    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(
        Config.META_APP_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    received = signature.split("=", 1)[1]

    return hmac.compare_digest(expected, received)

@app.route("/webhook/meta", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if (mode == "subscribe" and token == Config.META_VERIFY_TOKEN):
        logger.info("Meta webhook verified")
        return challenge, 200

    return "Verification failed", 403

@app.route("/webhook/meta", methods=["POST"])
def receive_webhook():
    raw_body = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_meta_signature(raw_body, signature):
        logger.warning("Invalid Meta webhook signature")
        return jsonify({"error": "Invalid signature"}), 403

    event = request.get_json(silent=True)
    if not event:
        return jsonify({"error": "Invalid JSON"}), 400

    if event.get("object") != "page":
        return jsonify({"status": "ignored"}), 200

    errors = []
    for entry in event.get("entry", []):
        page_id = entry.get("id")
        for change in entry.get("changes", []):
            if change.get("field") != "leadgen":
                continue

            value = change.get("value", {})
            lead_id = value.get("leadgen_id")

            if not lead_id:
                continue

            try:
                if is_processed(lead_id):
                    logger.info(
                        "Lead already processed: %s",
                        lead_id
                    )
                    continue

                logger.info("New Instagram lead: %s", lead_id)
                lead = get_lead_details(lead_id)
                payload = create_crm_payload(
                    lead,
                    page_id=page_id
                )

                crm_result = send_to_crm(payload)
                save_lead_status(
                    lead_id=lead_id,
                    status="success",
                    crm_id=crm_result.get("ID")
                )

                logger.info(
                    "Lead sent to CRM successfully. "
                    "Lead ID: %s, CRM ID: %s",
                    lead_id,
                    crm_result.get("ID")
                )

            except Exception as exc:
                logger.exception("Lead processing failed: %s", lead_id)

                save_lead_status(
                    lead_id=lead_id,
                    status="failed",
                    error=str(exc)[:1000]
                )
                errors.append(lead_id)

    if errors:
        return jsonify({"status": "partial_failure", "failed_leads": errors}), 500

    return jsonify({"status": "success", "message": "Webhook processed successfully"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
