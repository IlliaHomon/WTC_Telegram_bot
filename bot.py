import database
import logging
import re
from telegram import Update, BotCommand, LinkPreviewOptions
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
        BotCommand("delete_recipes","Delete 1 or more recipes"),
        BotCommand("delete_all_recipes", "Delete all your recipes"), 
        BotCommand("search","Search recipes by keyword"),
        BotCommand("all_recipes","Titles of all your recipes"),
        BotCommand("all_recipes_in_category","List of recipes in a category"),
        BotCommand("categories","View all recipe categories you have added"),
        BotCommand("generate_plan","Generate a new meal plan"),
        BotCommand("cancel","Cancel current action"),
        BotCommand("my_family_id","Get your family id"),
        BotCommand("join_family","Join a family via family id"),
        BotCommand("leave_family","Leave your current family"),
        BotCommand("what_is_family","Info on what is a family and what it's for"),
        BotCommand("family_members", "All users in your family"),
        BotCommand("commands","Get a list of all commands")
    ]
    await application.bot.set_my_commands(commands)

#-----------------------------------------------

#The start function

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.init_db()
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    if(not database.user_has_family(user_id)):
        database.create_family(user_id, username)
    database.get_user_family_id(user_id,username) #To trigger the username saving

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
        "📋All the commands available for WTC bot:\n\n"
        "🍽 Recipes-related commands:\n"
        "• /add_recipe - Add a new recipe, Title on line 1 and Category on line 2 are mandatory, adding instructions on line 3 is optional. Recipes you add can be accessed by all members of your family\n"
        "• /delete_recipes - Delete a recipe, or multiple recipes. It is possible to remove any recipe in a family, including the ones added by other members\n"
        "• /delete_all_recipes - Delete all recipes in a family\n"
        "• /search - Search recipes by title\n"
        "• /all_recipes - Titles of all recipes in a family\n"
        "• /all_recipes_in_category - A list of all recipes in the category\n"
        "• /categories - Get names of all recipe categories your family created\n\n"
        "👨‍👩‍👦 Family-related commands:\n"
        "• /my_family_id - Get your family id. family_id is assigned automatically when you run your first command\n"
        "• /join_family - join another user's family\n"
        "• /leave_family - leave your current family (You dont need to\n"
        "do it if you want to join another family, just use /join_family.\n"
        "If you leave a family a new family_id will be assigned automatically)\n"
        "• /family_members - get a list of all current members of your family\n"
        "• /what_is_family - Get all information about what is a family and what's it for\n\n"
        "⚙️ Other commands:\n"
        "• /generate_plan - Generate a meal plan. Requires total recipe count on line 1. Optionally add specific recipe titles on line 2, and category requirements (e.g., 2 Soup) on line 3."  
    )
    await update.message.reply_text(text)

#Family-related functions

async def get_my_family_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    family_id = database.get_user_family_id(user_id,username)
    if(family_id is None):
        family_id = database.create_family(user_id,username)
    reply = "Your family id: " + family_id
    await update.message.reply_text(reply)

#Functions to join a family

async def join_family_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👨‍👩‍👧‍👦Please provide the family id")
    return 1

async def join_family_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    family_id = update.message.text.strip()
    username = update.effective_user.username or update.effective_user.first_name
    current_family_id = database.get_user_family_id(user_id,username)
    if(current_family_id == family_id):
        await update.message.reply_text(f"You are already a part of family {family_id}")
        return ConversationHandler.END
    else:
        joined_successfully = database.assign_family_id(user_id, family_id, username)
        if joined_successfully:
            await update.message.reply_text(f"✅Successfully joined family {family_id}!")
            return ConversationHandler.END
        else:
            await update.message.reply_text("❌ERROR No family was found with such family id, try again")
            return 1

#-----------------------------------------------

async def leave_family(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    database.leave_family(user_id,username)
    await update.message.reply_text("✅Successfully left! Use /my_family_id to get your new family id")

async def get_family_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👨‍👩‍👦Family is a convenient WTC bot feature that lets multiple\n" \
                                    "users to access joint recipe database, which means that\n" \
                                    "you, your boyfriend/girlfriend/husband/wife, your friends,\n"
                                    "grandmother or even an aunt you've never seen in your life\n" \
                                    "can access the shared recipes to generate meal plans, search\n" \
                                    "for recipes your grandma cooked 20 years ago, or any other\n" \
                                    "purpose you can come up with! Enjoy using WTC bot!")

async def get_family_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    family_id = database.get_user_family_id(user_id,username)
    if family_id is None:
        family_id = database.create_family(user_id,username)
    all_usernames = database.get_all_usernames(family_id)
    reply_text = "⚠️Note WTC bot can only catch users username\nif they run a command\n\n👨‍👩‍👦Here is the list of all members of your family:\n\n"
    if all_usernames:
        for index,name in enumerate(all_usernames,start=1):
            reply_text += f"{index}. {name}\n"
    else: reply_text = "No members found."

    await update.message.reply_text(reply_text)

#-----------------------------------------------
    
#A function to cancel multi-step action(Conversation)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫Cancelled.")
    return ConversationHandler.END

#-----------------------------------------------

#Conversation interupters

async def adding_conversation_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳Please finnish adding the recipe first\n/cancel to exit")
    return 1

async def deleting_conversation_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳Please finnish deleting the recipe first\n/cancel to exit")
    return 1

async def deleting_my_recipes_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳Please finnish deleting all your recipes first\n/cancel to exit")
    return 1

async def generating_plan_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳Please finnish generating a plan first\n/cancel to exit")
    return 1

async def search_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳Please finnish searching first\n/cancel to exit")
    return 1

async def all_recipes_in_category_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳Please finnish your current action first\n/cancel to exit")
    return 1

async def join_family_interupt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳Please finnish joining family first\n/cancel to exit")
    return 1

#-----------------------------------------------

#Two functions to add recipes

async def add_recipe(update:Update, context: ContextTypes.DEFAULT_TYPE)->int:
    bot_message = (
        "➕To add a recipe please send it using the following format:\n\n"
        "•Title\n"
        "•Recipe category (e.g Soup,Main,Salad etc.)\n"
        "•Instructions(Can be a link)\n\n"
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
        username = update.effective_user.username or update.effective_user.first_name
        family_id = database.get_user_family_id(user_id,username)
        if family_id is None:
                family_id = database.create_family(user_id,username)
        
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
        "🗑️Please send titles of recipes/recipe you want to delete in the following format:\n\n"
        "•Title 1\n"
        "•Title 2\n"
        "•etc.\n\n"
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
        username = update.effective_user.username or update.effective_user.first_name
        family_id = database.get_user_family_id(user_id,username)
        if family_id is None:
            family_id = database.create_family(user_id,username)

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

async def delete_recipes_response(update:Update, context: ContextTypes.DEFAULT_TYPE)->int:
    await update.message.reply_text("⚠️Are you sure you want to delete ALL recipes you added? Y/N:")
    return 1

async def delete_recipes_action(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text.lower() == "y":
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        family_id = database.get_user_family_id(user_id,username)
        if family_id is None:
            family_id = database.create_family(user_id,username)

        number_of_deleted_recipes = database.delete_all_recipes(user_id,family_id)
        if number_of_deleted_recipes > 0:
            await update.message.reply_text(f"✅All {number_of_deleted_recipes} recipes deleted successfully!")
        else:
            await update.message.reply_text("❌ERROR No recipes to delete")
        return ConversationHandler.END
    elif user_text.lower() == "n":
        await update.message.reply_text("Cancelled.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ERROR Please respond with either Y to proceed with deletion\n or N to cancel!")
        return 1

#-----------------------------------------------

# Search functions

async def search_response(update:Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍Please provide the search request(e.g Pasta Carbonara)\n/cancel to exit")
    return 1

async def search_action(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    family_id = database.get_user_family_id(user_id,username)
    if family_id is None:
        family_id = database.create_family(user_id,username)
    
    user_search = update.message.text
    results = database.search_recipes_by_title(user_search, user_id, family_id)
    if not results:
        await update.message.reply_text("❌ERROR No recipe found by that keyword")
        return ConversationHandler.END

    formatted_recipes = []
    for title, category, instructions in results:
        card = f"--------------------\n{title} ({category})"
        if instructions and instructions.strip():
            card += f"\n\n{instructions.strip()}"
        card += "\n--------------------"
        formatted_recipes.append(card)

    answer = "\n\n" + "\n\n".join(formatted_recipes)
    await update.message.reply_text(answer, link_preview_options=LinkPreviewOptions(is_disabled=True))
    return ConversationHandler.END
#-----------------------------------------------

#Functions to list all recipes in a category

async def all_recipes_in_category_response(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧾Please provide the category")
    return 1

async def all_recipes_in_category_action(update:Update, context:ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    family_id = database.get_user_family_id(user_id,username)
    if family_id is None:
        family_id = database.create_family(user_id,username)
    
    user_request = update.message.text.strip()
    results = database.search_recipes_by_category(user_request, user_id, family_id)
    if not results:
        await update.message.reply_text("❌ERROR No recipe found by that category")
        return ConversationHandler.END

    formatted_recipes = []
    for title, category, instructions in results:
        card = f"--------------------\n{title} ({category})"
        if instructions and instructions.strip():
            card += f"\n\n{instructions.strip()}"
        card += "\n--------------------"
        formatted_recipes.append(card)

    header = f"📃All recipes in the '{user_request}' category:\n\n"
    answer = header + "\n\n".join(formatted_recipes)
    await update.message.reply_text(answer, link_preview_options=LinkPreviewOptions(is_disabled=True))
    return ConversationHandler.END

#-----------------------------------------------

#A function to list all titles of recipes available to user

async def all_recipes(update:Update, context:ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    family_id = database.get_user_family_id(user_id,username)
    if family_id is None:
        family_id = database.create_family(user_id,username)

    all_titles = database.get_all_recipes(user_id,family_id)

    if all_titles:
        reply_text = "🍽Here are the titles of all recipes available to you:\n\n"
        for index,title in enumerate(all_titles,start=1):
            reply_text += f"{index}. {title}\n"
    else: reply_text = "❌ERROR No recipe found, use /add_recipe to add a new recipe!"

    await update.message.reply_text(reply_text)

#-----------------------------------------------

#A function to list all recipe categories the user added

async def categories(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    family_id = database.get_user_family_id(user_id,username)
    if family_id is None:
        family_id = database.create_family(user_id,username)
    results = database.get_all_categories(user_id,family_id)
    category_names=[cat for cat in results]

    if not category_names:
        await update.message.reply_text("❌ERROR No categories found. Add recipes with /add_recipe first!")
        return
    formatted_results = "• " + "\n• ".join(category_names)
    await update.message.reply_text(f"📃Here are all categories you've added: \n\n{formatted_results}")

#-----------------------------------------------

#Functions to generate the meal plan

async def generate_plan_response(update:Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧑‍🍳To generate a plan, please provide the information in the following format:\n\n"
                                    "•How many recipes\n"
                                    "•Names of the recipes that you want to be included(e.g Pasta Carbonara, Cheese Soup)\n"
                                    "•How much and of which category, recipes should be included(e.g 2 Soup, 1 Salad)\n\n"
                                    "/cancel to exit")
    return 1

async def generate_plan_action(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    lines = [line.strip() for line in user_text.split('\n') if line.strip()]

    try:
        total_count = int(lines[0])
    except IndexError:
        await update.message.reply_text("❌ERROR: Please provide at least how many recipes a plan should have, everything else is optional\n/cancel to exit")
        return 1
    except ValueError:
        await update.message.reply_text("❌ERROR: Please provide a valid number of recipes(e.g 3, 5, 7)")
        return 1

    mandatory_titles = []
    category_counts = {}

    if len(lines) > 1:
        mandatory_titles = [t.strip() for t in lines[1].split(',') if t.strip()]

    if len(lines) > 2:
        matches = re.findall(r'(\d+)\s+([a-zA-Z0-9\s]+)', lines[2]) #re is regex, it finds all matches for the blueprint (\d+) is 1 or more digits, () defines capturing group
                                                                    #\s+ is for 1 or more spaces and ([a-zA-Z0-9\s]+) stands for a sequence of 1 or more characters where each is either a-z, A-Z or 0-9
        for count_str, category_name in matches:
            category_counts[category_name.strip().lower()] = int(count_str)

    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    family_id = database.get_user_family_id(user_id, username)
    if family_id is None:
        family_id = database.create_family(user_id, username)

    mandatory_ids = database.get_recipe_ids_by_titles( user_id, family_id, mandatory_titles)

    plan = database.get_custom_meal_plan(
        user_id=user_id,
        family_id=family_id,
        mandatory_ids=mandatory_ids,
        category_counts=category_counts,
        total_count=total_count
    )

    if not plan:
        await update.message.reply_text("❌ No recipes found in your database to create a plan.")
        return ConversationHandler.END

    reply_text = f"📋 Generated Meal Plan ({len(plan)} meals):\n"
    for index, (r_id,title, category, instructions) in enumerate(plan, start=1):
        reply_text += f"\n----------------------------------------\n{index}. {title} ({category})\n"
        if instructions:
            reply_text += f"\n{instructions}\n"
        reply_text += "----------------------------------------\n"
    

    await update.message.reply_text(reply_text, link_preview_options=LinkPreviewOptions(is_disabled=True))
    return ConversationHandler.END
    


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
        entry_points=[CommandHandler("delete_recipes", delete_recipe_response)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_recipe_action)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),deleting_conversation_interupt)] 
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delete_all_recipes", delete_recipes_response)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_recipes_action)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),deleting_my_recipes_interupt)] 
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("generate_plan", generate_plan_response)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_plan_action)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"), generating_plan_interupt)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("search",search_response)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_action)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),search_interupt)] 
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("all_recipes_in_category", all_recipes_in_category_response)],
        states = {
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, all_recipes_in_category_action)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),all_recipes_in_category_interupt)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("join_family", join_family_response)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_family_action)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler(filters.COMMAND & ~filters.Regex(r"^/cancel$"),join_family_interupt)] 
    ))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("categories", categories))
    app.add_handler(CommandHandler("commands", get_all_commands))
    app.add_handler(CommandHandler("my_family_id", get_my_family_id))
    app.add_handler(CommandHandler("leave_family", leave_family))
    app.add_handler(CommandHandler("what_is_family", get_family_info))
    app.add_handler(CommandHandler("family_members", get_family_members))
    app.add_handler(CommandHandler("all_recipes", all_recipes))

    print("Bot is running...")
    app.run_polling()

# For importing the file to other files without starting the bot
if __name__ == "__main__":
    database.init_db()
    main()