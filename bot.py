import database
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    ApplicationHandlerStop,
)
import os
from dotenv import load_dotenv

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

WAITING_FOR_RESPONSE = 0

#A function to post the command list

async def post_init(application:Application):
    commands = [
        BotCommand("start","Start the bot"),
        BotCommand("add_recipe","Add a new recipe"),
        BotCommand("delete_recipe","Delete a recipe"),
        BotCommand("search","Search recipes by keyword"),
        BotCommand("list","List of recipes in a category"),
        BotCommand("categories","View all recipe categories you have added"),
        BotCommand("generate_plan","Generate a new meal plan"),
        BotCommand("cancel","Cancel current action")
    ]
    await application.bot.set_my_commands(commands)

#-----------------------------------------------

#The start function

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.init_db()
    welcome_text = (
        "👋 Welcome to Recipe Planner Bot!\n\n"
        "Here is what I can do:\n"
        "• /add_recipe - Step-by-step interactive recipe creation\n"
        "• /delete_recipe - Step-by-step interactive recipe removal\n"
        "• /search <keyword> - Search recipes by title\n"
        "• /list <category> - A list of all recipes in the category\n"
        "• /categories - List all stored recipe categories\n"
        "• /generate_plan- Generate a random meal plan\n"
        "• /cancel - Cancel current multi-step action"
    )
    await update.message.reply_text(welcome_text)   

#-----------------------------------------------
    
#A function to cancel multi-step action(Conversation)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

#-----------------------------------------------

#Conversation interupters

async def adding_conversation_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please finnish adding the recipe first\n/cancel to exit")
    return 1

async def deleting_conversation_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please finnish deleting the recipe first\n/cancel to exit")
    return 1

#-----------------------------------------------

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

#-----------------------------------------------

#A function to list all recipes in a category

async def list_recipes_in_category(update:Update, context:ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ERROR Please provide a category, for example: /list soup")
        return
    user_request = " ".join(context.args).strip()
    results = database.search_recipes_by_category(user_request, user_id)
    if not results:
        await update.message.reply_text("❌ERROR No recipe found by that category")
        return

    formatted_reipes=[
        f"--------------------\n{title}\n{category}\n\n{instructions}\n--------------------" for title,category,instructions in results
    ]

    answer = "\n\n" + "\n\n".join(formatted_reipes)
    await update.message.reply_text(answer)

#-----------------------------------------------

#A function to list all recipe categories the user added

async def categories(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    results = database.get_all_categories(user_id)
    category_names=[cat for cat in results]
    formatted_results = "• " + "\n• ".join(category_names)
    await update.message.reply_text(f"Here are all categories you've added: \n{formatted_results}")

#-----------------------------------------------

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_recipe", add_recipe)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_recipe),
                CommandHandler("add_recipe", adding_conversation_interupt),
                CommandHandler("delete_recipe", adding_conversation_interupt)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),adding_conversation_interupt)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delete_recipe", delete_recipe_response)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_recipe_action),
                CommandHandler("add_recipe", deleting_conversation_interupt),
                CommandHandler("delete_recipe", deleting_conversation_interupt)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),deleting_conversation_interupt)] 
    ))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("categories", categories))
    app.add_handler(CommandHandler("list", list_recipes_in_category))

    print("Bot is running...")
    app.run_polling()

# For importing the file to other files without starting the bot
if __name__ == "__main__":
    database.init_db()
    main()