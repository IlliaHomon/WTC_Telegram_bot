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
import os
from dotenv import load_dotenv

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

WAITING_FOR_RESPONSE = 0


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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

#Two functions to add recipes
async def add_recipe(update:Update, context: ContextTypes.DEFAULT_TYPE)->int:
    bot_message = (
        "To add a recipe please send it using the following format:\n"
        "\n"
        "Title\n"
        "Recipe category (e.g Soup,Main,Salad etc.)\n"
        "Instructions" 
    )
    await update.message.reply_text(bot_message)
    return 1

async def save_recipe(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    lines = user_text.split('\n')
    if(len(lines)>=2):
        Title = lines[0].strip()
        Category = lines[1].strip()
        Instructions = "\n".join(lines[2:]).strip() if len(lines)>2 else ""
        database.add_recipe(Title,Category,Instructions)
        await update.message.reply_text("✅Recipe added successfully!")
        return ConversationHandler.END
    else: 
        await update.message.reply_text("❌ERROR Recipe not added, try again")
        return 1



def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_recipe", add_recipe)],
        states={
            1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_recipe)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]    
    ))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()