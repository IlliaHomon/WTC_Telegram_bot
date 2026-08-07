import database
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = "REMOVED_TOKEN"

TITLE, CATEGORY, INSTRUCTIONS = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.init_db()
    welcome_text = (
        "👋 Welcome to Recipe Planner Bot!\n\n"
        "Here is what I can do:\n"
        "• /add_recipe - Step-by-step interactive recipe creation\n"
        "• /delete_recipe - Step-by-step interactive recipe removal\n"
        "• /search <keyword> - Search recipes by title\n"
        "• /categories - List all stored recipe categories\n"
        "• /generate_list- Generate a random meal plan\n"
        "• /cancel - Cancel current multi-step action"
    )
    await update.message.reply_text(welcome_text)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()