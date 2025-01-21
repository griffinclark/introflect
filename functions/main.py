from flask import Flask, request, jsonify
from src.functions.chat.chat_application import ChatApplication
import requests

# Import Firebase Functions
from firebase_functions.https import CallableRequest, on_call

app = Flask(__name__)
chat_app = ChatApplication(user_id="g")

@app.route("/", methods=["GET"])
def home():
    return "Telegram Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        user_input = update["message"]["text"]

        try:
            chat_app.chat(user_input)
            response_message = chat_app.chat_context.context[-1].content
        except Exception as e:
            response_message = f"Error: {e}"

        send_message(chat_id, response_message)

    return jsonify({"status": "ok"})

def send_message(chat_id, text):
    """
    Send a message to Telegram
    """
    TELEGRAM_API_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}"
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# Deploy the webhook
@on_call
def telegram_bot(request: CallableRequest):
    return app
