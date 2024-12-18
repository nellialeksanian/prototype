import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup #InputMediaPhoto, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)
from generation.generation_route import generate_route
from generation.generate_artwork_info import generate_artwork_info
from generation.generate_answer import generate_answer
from dotenv import load_dotenv
from validation.validation_QA import evaluate_hallucinations

from process_data.load_data import split_text

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'route_mode'
    context.user_data['current_artwork_index'] = 0
    keyboard = [
        [
            InlineKeyboardButton("С изображением", callback_data="with_images"),
            InlineKeyboardButton("Без изображения", callback_data="without_images"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Здравствуйте! Добро пожаловать в наш музей!\n"
        "Выберите, как вы хотите получать информацию о картинах:",
        reply_markup=reply_markup,
    )
    
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Обрабатываем выбор пользователя
    if query.data == "with_images":
        context.user_data['send_images'] = True
        await query.message.reply_text(
            "Вы выбрали режим с изображениями! Что бы вы хотели посмотреть в музее сегодня?"
        )
        
    elif query.data == "without_images":
        context.user_data['send_images'] = False
        await query.message.reply_text(
            "Вы выбрали режим без изображений! Что бы вы хотели посмотреть в музее сегодня?"
        )

    # Переход к следующему шагу после выбора формата
    context.user_data['state'] = 'route_mode'

# Function to handle user's initial input and generate the route
async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'route_mode':
        user_query = update.message.text
        #generating the route and artwork details
        route_and_artworks, context.user_data['artworks'] = generate_route(user_query, k=10)

        max_message_length = 4096
        route_and_artworks_parts = split_text(route_and_artworks, max_message_length)
        for part in route_and_artworks_parts:
            await update.message.reply_text(part)
        # send_images = context.user_data.get('send_images', False)
        # send the generated route to the user

        # ask if the user is ready to start the journey
        keyboard = [[InlineKeyboardButton("Да, я готов(а)", callback_data='next_artwork')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Вы готовы начать экскурсию?", reply_markup=reply_markup)
        
    elif context.user_data.get('state') == 'question_mode':
        user_question = update.message.text
        last_shown_artwork_index = context.user_data['last_shown_artwork_index']
        answer = generate_answer(user_question, context.user_data['artworks'][last_shown_artwork_index])
        validation_res = evaluate_hallucinations(context.user_data['artworks'][last_shown_artwork_index], answer, user_question)
        await update.message.reply_text(generate_answer(user_question, context.user_data['artworks'][last_shown_artwork_index]))
        print(f'validation result:{ validation_res}')

async def next_artwork(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    current_artwork_index = context.user_data['current_artwork_index']

    if current_artwork_index < len(context.user_data['artworks']):
        context.user_data['state'] = 'question_mode'
        
        context.user_data['last_shown_artwork_index'] = current_artwork_index
        artwork = context.user_data['artworks'][current_artwork_index]

        await query.answer()
        artwork_info = generate_artwork_info(artwork.get("text"))
        max_message_length = 4096 
        artworks_parts = split_text(artwork_info, max_message_length)
            
        # Получаем ссылку на изображение, если она есть
        image_url = artwork.get("image")  # Ссылка на изображение из базы данных
        caption = artworks_parts[0]
        
        # Обрезаем подпись, если она превышает 1024 символа
        if len(caption) > 1024:
            caption = caption[:1024]

        # Проверяем, нужно ли отправлять изображение
        if context.user_data.get('send_images', False) and image_url:
            # Если выбрано с изображениями и изображение существует
            await query.message.reply_photo(image_url, caption=caption)
        else:
            # Если выбрано без изображений или изображения нет
            await query.message.reply_text(caption)

        # Отправляем остальные части текста без изображения
        for part in artworks_parts[1:]:
            await query.message.reply_text(part)

        context.user_data['current_artwork_index'] += 1

        if context.user_data['current_artwork_index'] < len(context.user_data['artworks']):
            keyboard = [[InlineKeyboardButton("Следующая картина", callback_data='next_artwork')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Задайте вопрос о текущей картине или нажмите ниже, чтобы перейти к следующей.",
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text("Задайте вопрос о текущей картине. Это последняя картина нашего маршрута!")
    else:
        await query.answer("Это была последняя картина.")


def main():
    token = os.getenv("TELEGRAM_TOKEN")

    # Create the Application with the bot token
    app = ApplicationBuilder().token(token).build()
    # Register command handler

    app.add_handler(CommandHandler("start", start))
    
    app.add_handler(CallbackQueryHandler(handle_choice, pattern='^(with_images|without_images)$'))
    
    # Register message handler for initial user input (generating route)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(?!.*Следующая картина).*$") & ~filters.COMMAND, handle_user_input))

    # Register callback query handler for next artwork
    app.add_handler(CallbackQueryHandler(next_artwork, pattern='next_artwork'))
  
    # Print a message to the console to confirm the bot is running
    print("Museum Guide Bot is ready and running!")

    # Run the bot until manually stopped
    app.run_polling()

if __name__ == '__main__':
    main()
