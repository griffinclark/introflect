from flask import Flask, request, jsonify
from firebase_admin import initialize_app, firestore
import telebot
import os

# Initialize Firebase app
initialize_app()
db = firestore.client()

# Initialize Flask and Telebot
app = Flask(__name__)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Telegram Bot Token not set in environment variables.")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Command router
COMMANDS = {}

def register_command(command, handler):
    """Registers a command handler."""
    COMMANDS[command] = handler

def execute_command(message):
    """Executes a command if registered."""
    command = message.text.split(" ")[0]
    handler = COMMANDS.get(command)
    if handler:
        handler(message)
    else:
        bot.reply_to(message, "Sorry, I don't recognize that command.")

# Default message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handles incoming messages and routes commands."""
    if message.text.startswith("/"):
        execute_command(message)
    else:
        bot.reply_to(message, "I'm here to assist! Use /help to see available commands.")

@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    """Telegram webhook for handling updates."""
    if request.method == "POST":
        try:
            json_data = request.get_json(silent=True)
            if json_data:
                bot.process_new_updates([telebot.types.Update.de_json(json_data)])
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            print(f"Error processing Telegram webhook: {e}")
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid request method."}), 400

# Firebase interaction example
def get_user_data(message):
    """Fetch user data from Firestore."""
    user_uid = message.text.split(" ")[1] if len(message.text.split(" ")) > 1 else None
    if not user_uid:
        bot.reply_to(message, "Please provide a user UID. Usage: /get_user_data <UID>")
        return

    try:
        doc_ref = db.collection("users").document(user_uid)
        doc = doc_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
            bot.reply_to(message, f"User Data:\n{user_data}")
        else:
            bot.reply_to(message, f"No data found for UID: {user_uid}")
    except Exception as e:
        bot.reply_to(message, f"Error fetching user data: {e}")

def add_sample_data(message):
    """Add sample data to Firestore."""
    try:
        db.collection("users").document("sample_user").set({
            "name": "Sample User",
            "age": 30,
            "location": "Sample City"
        })
        bot.reply_to(message, "Sample data added successfully.")
    except Exception as e:
        bot.reply_to(message, f"Error adding sample data: {e}")

# Register commands
register_command("/get_user_data", get_user_data)
register_command("/add_sample_data", add_sample_data)

def app_main(request):
    return app(request)
