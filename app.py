from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load env variables
load_dotenv()

app = Flask(__name__)

# Config
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
DEFAULT_RECEIVER = os.getenv("DEFAULT_RECEIVER")
PORT = int(os.getenv("PORT", 5000))

# Validate env early (fail fast)
if not ACCOUNT_SID or not AUTH_TOKEN or not TWILIO_NUMBER:
    raise ValueError("Missing Twilio configuration in .env")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def normalize_whatsapp_number(num: str) -> str:
    """Ensure 'whatsapp:+<countrycode><number>' format."""
    if not num:
        return None
    num = num.strip()
    if not num.startswith("whatsapp:"):
        if not num.startswith("+"):
            # assume it's a raw number like 91XXXXXXXXXX
            num = "+" + num
        num = "whatsapp:" + num
    return num

@app.route("/", methods=["GET"])
def health():
    return {"status": "alive"}
    
@app.route("/send", methods=["POST"])
def send_message():
    data = request.get_json(silent=True) or {}

    message_text = data.get("message")
    if not message_text:
        return jsonify({
            "status": "error",
            "error": "Field 'message' is required"
        }), 400

    # Optional override; else fallback to your number
    receiver = data.get("to") or DEFAULT_RECEIVER
    receiver = normalize_whatsapp_number(receiver)

    try:
        msg = client.messages.create(
            from_=TWILIO_NUMBER,
            body=message_text,
            to=receiver
        )

        return jsonify({
            "status": "sent",
            "to": receiver,
            "sid": msg.sid
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
