from dotenv import load_dotenv
from typing import Final
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.functions.chat.chat_application import ChatApplication


# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("TELEGRAM_BOT_USERNAME")
chat_app = ChatApplication(user_id="g", max_context_tokens=10000, debug=False)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hello! I am {BOT_USERNAME}. Type anything to chat with me!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This bot doesn't have much functionality yet. Good luck!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send "Thinking..." message immediately
    thinking_message = await update.message.reply_text("🧠 Thinking...")

    # Handle incoming messages
    message_type: str = update.message.chat.type
    text: str = update.message.text.strip()  # Remove extra spaces
    
    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    # Use ChatApplication to generate a response
    try:
        chat_app.chat(text)  # Process the user's input
        response = chat_app.output_manager.logs[-1]  # Get the last logged response
    except Exception as e:
        response = f"An error occurred: {str(e)}"
    
    print('Bot:', response)

    # Edit the "Thinking..." message with the actual response
    await thinking_message.edit_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle errors in the bot
    print(f"Update {update} caused error {context.error}")

if __name__ == "__main__":
    print("Starting bot...")
    
    # Initialize bot application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Message handler for text messages (excluding commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    app.add_error_handler(error)

    print("Polling...!")
    app.run_polling(poll_interval=3)
