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
        BotCommand("delete_all_my_recipes", "Delete all your recipes"), 
        BotCommand("search","Search recipes by keyword"),
        BotCommand("list","List of recipes in a category"),
        BotCommand("categories","View all recipe categories you have added"),
        BotCommand("generate_plan","Generate a new meal plan"),
        BotCommand("cancel","Cancel current action"),
        BotCommand("my_family_id","Get your family id"),
        BotCommand("join_family","Join a family via family id"),
        BotCommand("leave_family","Leave your current family"),
        BotCommand("what_is_family","Info on what is a family and what it's for"),
        BotCommand("commands","Get a list of all commands"),
        BotCommand("all_my_recipes","Titles of all your recipes"),
        BotCommand("family_members", "All users in your family")
    ]
    await application.bot.set_my_commands(commands)

#-----------------------------------------------

#The start function

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.init_db()
    user_id = update.effective_user.id
    if(not database.user_has_family(user_id)):
        database.create_family(user_id)
    welcome_text = (
        "👋 Welcome to Recipe Planner Bot!\n\n"
        "👨‍👩‍👦 If you are a new user you will be assigned a family id 👨‍👩‍👦\n"
        "🧩 Use /commands to get info abbout all the commands\n"
        "💞Enjoy using the WTC Bot!💞"
    )
    await update.message.reply_text(welcome_text)   

#-----------------------------------------------

async def get_all_commands(update:Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "All the commands available for WTC bot:\n\n"
        "👨‍👩‍👦 Family-related commands:\n"
        "• /my_family_id - get your family id\n"
        "• /join_family <family_id> - join another family\n"
        "• /leave_family - leave your current family(You dont need to\n"
        "do it if you want to join another family, just use /join_family.\n"
        "If you leave a family a new family_id will be assigned automatically)\n"
        "• /what_is_family - explains what is a family and what's it for\n"
        "• /family_members - get a list of all current members of your family\n\n"
        "🍽 Recipes-related commands:\n"
        "• /add_recipe - Step-by-step interactive recipe creation\n"
        "• /delete_recipe - Step-by-step interactive recipe removal\n"
        "• /delete_all_my_recipes - Deletes all your recipes\n"
        "• /search <keyword> - Search recipes by title\n"
        "• /all_my_recipes - Titles of all your recipes\n"
        "• /list <category> - A list of all recipes in the category\n"
        "• /categories - List all stored recipe categories\n\n"
        "⚙️ All other commands:\n"
        "• /generate_plan- Generate a random meal plan"     
    )
    await update.message.reply_text(text)

#Family-related functions

async def get_my_family_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    family_id = database.get_user_family_id(user_id)
    if(family_id is None):
        family_id = database.create_family(user_id)
    reply = "Your family id: " + family_id
    await update.message.reply_text(reply)

async def join_family(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ERROR Please provide a family id, for example: /join_family A1A1A1")
        return
    family_id = " ".join(context.args).strip()
    current_family_id = database.get_user_family_id(user_id)
    if(current_family_id == family_id):
        await update.message.reply_text("You are already a part of that family")
    else:
        joined_successfully = database.assign_family_id(user_id, family_id)
        if joined_successfully:
            await update.message.reply_text("✅Successfully joined!")
        else:
            await update.message.reply_text("❌ERROR No family was found with such family id")

async def leave_family(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    database.leave_family(user_id)
    await update.message.reply_text("✅Successfully left! Use /my_family_id to get your new family id")

async def get_family_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👨‍👩‍👦Family is a convenient WTC bot feature that lets multiple\n" \
                                    "users to access joint recipe database, which means that\n" \
                                    "you, your boyfriend/girlfriend/husband/wife, your friends,\n"
                                    "grandmother or even an aunt you've never seen in your life\n" \
                                    "can access the shared recipes to generate meal plans, search\n" \
                                    "for recipes your grandma cooked 20 years ago, or any other\n" \
                                    "purpose you can come up with! Enjoy using WTC bot!")
    
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

async def deleting_my_recipes_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please finnish deleting all your recipes first\n/cancel to exit")

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
        user_id = update.effective_user.id
        family_id = database.get_user_family_id(user_id)
        if family_id is None:
                family_id = database.create_family(user_id)
        
        database.add_recipe(user_id ,Title,family_id,Category,Instructions)
        await update.message.reply_text("✅Recipe added successfully!")
        return ConversationHandler.END
    else: 
        await update.message.reply_text("❌ERROR Recipe not added, check the format and try again")
        return 1

#------------------------------------------------

# Two functions to delete a recipe

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
    lines = [line.strip() for line in lines if line.strip()]
    if len(lines)>0:
        user_id = update.effective_user.id
        family_id = database.get_user_family_id(user_id)
        if family_id is None:
            family_id = database.create_family(user_id)

        has_error = False
        for title in lines: 
            if database.delete_recipe(title, user_id, family_id):
                await update.message.reply_text(f"✅{title} deleted successfully!")
            else: 
                await update.message.reply_text(f"❌ERROR {title} not deleted, check if there is a recipe with such name and try again\n/cancel to exit")
                has_error = True

        if has_error: return 1
        return ConversationHandler.END
    else: 
        await update.message.reply_text(f"❌ERROR No recipe was given to delete, try again\n/cancel to exit")
        return 1
        
#-----------------------------------------------

#Two functions to delete all recipes added by user

async def delete_my_recipes_response(update:Update, context: ContextTypes.DEFAULT_TYPE)->int:
    await update.message.reply_text("Are you sure you want to delete ALL recipes added by you? Y/N:")
    return 1

async def delete_my_recipes_action(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text.lower() == "y":
        user_id = update.effective_user.id
        number_of_deleted_recipes = database.delete_all_user_recipes(user_id)
        if number_of_deleted_recipes > 0:
            await update.message.reply_text(f"✅All {number_of_deleted_recipes} recipes deleted successfully!")
        else:
            await update.message.reply_text("❌ERROR No recipes to delete")
        return ConversationHandler.END
    elif user_text.lower() == "n":
        await update.message.reply_text("Cancelled successfully")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ERROR Please respond with either Y to proceed with deletion\n or N to cancel!")
        return 1

#-----------------------------------------------

# Searching function

async def search(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    family_id = database.get_user_family_id(user_id)
    if family_id is None:
        family_id = database.create_family(user_id)
    if not context.args:
        await update.message.reply_text("❌ERROR Please provide a keyword, for example: /search pasta")
        return
    user_search = " ".join(context.args).strip()
    results = database.search_recipes_by_title(user_search, user_id, family_id)
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
    family_id = database.get_user_family_id(user_id)
    if family_id is None:
        family_id = database.create_family(user_id)
    if not context.args:
        await update.message.reply_text("❌ERROR Please provide a category, for example: /list soup")
        return
    user_request = " ".join(context.args).strip()
    results = database.search_recipes_by_category(user_request, user_id, family_id)
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
    family_id = database.get_user_family_id(user_id)
    if family_id is None:
        family_id = database.create_family(user_id)
    results = database.get_all_categories(user_id,family_id)
    category_names=[cat for cat in results]
    formatted_results = "• " + "\n• ".join(category_names)
    await update.message.reply_text(f"Here are all categories you've added: \n{formatted_results}")

#-----------------------------------------------

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_recipe", add_recipe)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_recipe)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),adding_conversation_interupt)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delete_recipe", delete_recipe_response)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_recipe_action)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),deleting_conversation_interupt)] 
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delete_all_my_recipes", delete_my_recipes_response)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_my_recipes_action)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),deleting_my_recipes_interupt)] 
    ))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("categories", categories))
    app.add_handler(CommandHandler("list", list_recipes_in_category))
    app.add_handler(CommandHandler("commands", get_all_commands))
    app.add_handler(CommandHandler("my_family_id", get_my_family_id))
    app.add_handler(CommandHandler("join_family", join_family))
    app.add_handler(CommandHandler("leave_family", leave_family))
    app.add_handler(CommandHandler("what_is_family", get_family_info))

    print("Bot is running...")
    app.run_polling()

# For importing the file to other files without starting the bot
if __name__ == "__main__":
    database.init_db()
    main()