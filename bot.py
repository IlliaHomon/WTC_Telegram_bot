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
        "Instructions\n\n"
        "/cancel to exit" 
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
        User_ID = update.effective_user.id
        database.add_recipe(User_ID ,Title,Category,Instructions)
        await update.message.reply_text("✅Recipe added successfully!")
        return ConversationHandler.END
    else: 
        await update.message.reply_text("❌ERROR Recipe not added, check the format and try again")
        return 1

#------------------------------------------------

# Two functions to delete recipes

async def delete_recipe_response(update:Update, context: ContextTypes.DEFAULT_TYPE)->int:
    bot_message = (
        "Please send titles of recipes/recipe you want to delete in the following format:\n"
        "\n"
        "Title 1\n"
        "Title 2\n"
        "etc.\n\n"
        "/cancel to exit" 
    )
    await update.message.reply_text(bot_message)
    return 1

async def delete_recipe_action(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    lines = user_text.split('\n')
    for line in lines: line.strip()
    if len(lines)>0:
        user_id = update.effective_user.id
        for title in lines: 
            if database.delete_recipe(title, user_id):
                await update.message.reply_text(f"✅{title} deleted successfully!")
            else: 
                await update.message.reply_text(f"❌ERROR {title} not deleted, check if there is a recipe with such name and try again")
                return 1
        return ConversationHandler.END
    else: 
        await update.message.reply_text(f"❌ERROR No recipe was given to delete, try again")
        return 1
        
#-----------------------------------------------

# Searching function

async def search(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ERROR Please provide a keyword, for example: /search pasta")
        return
    user_search = " ".join(context.args).strip()
    results = database.search_recipes_by_title(user_search, user_id)
    if not results:
        await update.message.reply_text("❌ERROR No recipe found by that keyword")
        return

    formatted_reipes=[
        f"--------------------\n{title}\n{category}\n\n{instructions}\n--------------------" for title,category,instructions in results
    ]

    answer = "\n\n" + "\n\n".join(formatted_reipes)
    await update.message.reply_text(answer)




def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_recipe", add_recipe)],
        states={
            1: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_recipe)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]    
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delete_recipe", delete_recipe_response)],
        states={
            1:[
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_recipe_action)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]    
    ))
    
    print("Bot is running...")
    app.run_polling()

# For importing the file to other files without starting the bot
if __name__ == "__main__":
    database.init_db()
    main()