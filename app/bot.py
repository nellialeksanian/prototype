import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
from generation.generation_route import generate_route
from embeddings.embeddings_similarity import search
from generation.generate_artwork_info import generate_artwork_info
from generation.generate_answer import generate_answer
from dotenv import load_dotenv

load_dotenv()

# Function to greet user and ask what they want to see
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'route_mode'
    context.user_data['current_artwork_index'] = 0
    
    await update.message.reply_text(
        "Здравствуйте! Добро пожаловать в наш музей! Что бы вы хотели посмотреть в музее сегодня?"
    )

# Function to handle user's initial input and generate the route
async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'route_mode':
        user_query = update.message.text
        # Use the external function to generate the route and artwork details
        route_and_artworks, context.user_data['artworks'] = generate_route(user_query, k=10)
        
        # Send the generated route to the user
        await update.message.reply_text(route_and_artworks)

        # Ask if the user is ready to start the journey
        keyboard = [[InlineKeyboardButton("Да, я готов(а)", callback_data='start_journey')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Вы готовы начать экскурсию?", reply_markup=reply_markup)
    elif context.user_data.get('state') == 'question_mode':
        context.user_data['current_artwork_index'] -= 1
        user_question = update.message.text
        current_artwork_index = context.user_data['current_artwork_index']
        # Handle normal user question input
        await update.message.reply_text(generate_answer(user_question, context.user_data['artworks'][current_artwork_index]))

# Function to start the journey and provide the first artwork information
async def start_journey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Switch user state to "question mode"
    context.user_data['state'] = 'question_mode'
    # Placeholder for the first artwork info, assuming this data is in the generated route
    artwork_info = generate_artwork_info(context.user_data['artworks'][0])
    context.user_data['current_artwork_index'] += 1

    await query.edit_message_text(text=artwork_info)

    # Ask if the user has questions
    await query.message.reply_text("У вас есть вопросы о первой картине? Напишите ваш вопрос или нажмите 'Следующая картина'.")

    # Next artwork button
    keyboard = [[InlineKeyboardButton("Следующая картина", callback_data='next_artwork')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Нажмите ниже чтобы перейти к следующей картине.", reply_markup=reply_markup)

async def next_artwork(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    query = update.callback_query
    current_artwork_index = context.user_data['current_artwork_index'] 
    
    if current_artwork_index < len(context.user_data['artworks']) - 1:

        context.user_data['state'] = 'question_mode'
    
        await query.message.reply_text(generate_artwork_info(context.user_data['artworks'][current_artwork_index]))
        current_artwork_index += 1 
        context.user_data['current_artwork_index'] = current_artwork_index

        query = update.callback_query
        await query.answer()

        # Ask if the user has questions
        await query.message.reply_text("У вас есть вопросы о следующей картине? Напишите ваш вопрос или нажмите 'Следующая картина'.")

        # Option for the next artwork
        keyboard = [[InlineKeyboardButton("Следующая картина", callback_data='next_artwork')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Нажмите ниже чтобы перейти к следующей картине.", reply_markup=reply_markup)
    else:
        await query.message.reply_text("Маршрут окончен. Надеюсь вам понравилось!")

# Main function to set up the bot
def main():
    token = os.getenv("TELEGRAM_TOKEN")
    # Create the Application with the bot token
    app = ApplicationBuilder().token(token).build()
    
    # Register command handler
    app.add_handler(CommandHandler("start", start))
    
    # Register message handler for initial user input (generating route)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(?!.*Следующая картина).*$") & ~filters.COMMAND, handle_user_input))
    
    # Register callback query handler for starting the journey
    app.add_handler(CallbackQueryHandler(start_journey, pattern='start_journey'))

    # Register callback query handler for next artwork
    app.add_handler(CallbackQueryHandler(next_artwork, pattern='next_artwork'))
    
    # Register the message handler for user questions ONLY after the user starts the journey
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_question))
    
    # Print a message to the console to confirm the bot is running
    print("Museum Guide Bot is ready and running!")

    # Run the bot until manually stopped
    app.run_polling()

if __name__ == '__main__':
    main()
