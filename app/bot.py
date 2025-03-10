import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)

from dotenv import load_dotenv
from generation.generation_route import generate_route
from generation.generate_artwork_info import generate_artwork_info
from generation.generate_voice import converter_text_to_voice
from generation.generate_answer import generate_answer, generate_answer_max
from process_data.load_data import send_text_in_chunks
from generation.generate_goodbye_word import exhibition_description, generate_goodbye_word
from validation.validation_QA import evaluate_hallucinations
from validation.validation_artworkinfo import evaluate_hallucinations_artworkinfo
import random 
import re
load_dotenv()


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data) for text, data in buttons]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.update({'state': 'route_mode', 'current_artwork_index': 0})
    keyboard = [["Старт"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Привет! 👋 Я твой виртуальный гид по виртуальной выставке 'Моя Третьяковка'. Моя цель — провести тебя по музею и рассказать об экспонатах и истории, которые делают каждую выставку уникальной.\n"
        "\n"
        "Но сначала давай познакомимся! Расскажи немного о себе: сколько тебе лет, чем ты увлекаешься? "
        "Что тебя привело в музей — ты здесь ради вдохновения, учебы или просто решил(а) интересно провести время? "
        "Чем больше я о тебе узнаю, тем более персонализированной будет твоя экскурсия! 😊", reply_markup = reply_markup
    )
    context.user_data['state'] = 'awaiting_description'

async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')

    if state == 'awaiting_description':
        context.user_data['user_description'] = update.message.text  # Сохраняем описание пользователя
        keyboard = create_keyboard([
            ("С изображением", "with_images"), 
            ("Без изображения", "without_images")
        ])
        await update.message.reply_text(
            "Я очень рад с вами познакомиться! Теперь осталось лишь выбрать удобный формат экскурсии, и мы сможем приступить!\n\n"
            "Выберите формат информации об экспонатах:",
            reply_markup=keyboard
        )
        context.user_data['state'] = 'awaiting_format'
    elif state == 'route_mode':
        await update.message.reply_text("Подождите немного, я готовлю ваш маршрут... ⏳")
        user_query = update.message.text
        user_description = context.user_data.get('user_description', '')
        top_k = context.user_data.get('top_k', 5)
        route, artworks = generate_route(top_k, user_description, user_query)
        context.user_data['artworks'] = artworks

        clean_route_for_gen = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', route)
        clean_route = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,:"«»]', '', route)
        voice_route = await converter_text_to_voice(clean_route_for_gen)
        
        await send_text_in_chunks(clean_route, lambda text: update.message.reply_text(text, parse_mode="Markdown"))
        await update.message.reply_voice(voice_route)
        
        with open("data/Slovcova/route.jpg", "rb") as photo: 
            await update.message.reply_photo(photo, caption="Карта маршрута")

        await update.message.reply_text(
            "Вы готовы начать экскурсию?", 
            reply_markup=create_keyboard([("Да, я готов(а)", "next_artwork")])
        )
    elif state == 'question_mode':
        await process_question(update, context)

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['send_images'] = query.data == "with_images" 
    await query.answer()

    keyboard = create_keyboard([
        ("🕒 Экспресс", "short"),
        ("⏳ Стандарт", "medium"),
        ("🕰 Полное погружение", "long")
    ])
    
    await query.message.reply_text(
        "Отличный выбор! Теперь выберите продолжительность экскурсии:",
        reply_markup=keyboard
    )

    context.user_data['state'] = 'awaiting_tour_length'


async def handle_tour_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tour_lengths = {
        "short": random.randint(3, 7),
        "medium": random.randint(8, 12),
        "long": random.randint(13, 20)
    }
    
    context.user_data['top_k'] = tour_lengths[query.data]  # Сохраняем выбранную длину экскурсии
    context.user_data['state'] = 'route_mode'

    await query.message.reply_text("Что бы вы хотели посмотреть в музее сегодня?")
    
async def process_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text
    index = context.user_data['last_shown_artwork_index']
    artwork = context.user_data['artworks'][index]
    user_description = context.user_data.get('user_description', '')
    await update.message.reply_text("Обрабатываю ваш вопрос... Подождите немного! ⏳")
    answer = generate_answer(user_question, artwork, user_description)
    validation_res = evaluate_hallucinations(artwork.get("text"), answer, user_question)
    print(f'validation result:{ validation_res}')

    if validation_res.lower() == "false":
        clean_answer = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', answer) 
        voice_answer = await converter_text_to_voice(clean_answer)
        await update.message.reply_text(answer, parse_mode="Markdown")
        await update.message.reply_voice(voice_answer)

    else: 
        answer_max = generate_answer_max(user_question, artwork, user_description)
        secondary_validation_res = evaluate_hallucinations(artwork.get("text"), answer_max, user_question)
        if secondary_validation_res.lower() == "false":
            await update.message.reply_text(answer_max)
            clean_answer_max = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', answer_max) 
            voice_answer_max = await converter_text_to_voice(clean_answer_max)
            await update.message.reply_voice(voice_answer_max)    
            print(f'secondary validation result:{ secondary_validation_res}')
        else: 
            await update.message.reply_text("К сожалению, я затрудняюсь ответить. Пожалуйста перефразируйте ваш вопрос.")

    current_artwork_index = context.user_data['current_artwork_index']
    if current_artwork_index < len(context.user_data['artworks']):
        keyboard = [[InlineKeyboardButton("Следующий экспонат", callback_data='next_artwork')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Вы можете задать ещё вопросы или перейти к следующему экспонату", reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("Завершить маршрут", callback_data='end_tour')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Вы можете задать ещё вопросы. Это последний экспонат!", reply_markup=reply_markup)

async def next_artwork(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    current_artwork_index = context.user_data['current_artwork_index']
    context.user_data['state'] = 'question_mode'
    context.user_data['last_shown_artwork_index'] = current_artwork_index
    artwork = context.user_data['artworks'][current_artwork_index]

    await query.answer()
    user_description = context.user_data.get('user_description', '')
    await query.message.reply_text("Обрабатываю ваш вопрос... Подождите немного! ⏳")
    artwork_info = generate_artwork_info(artwork.get("text"), user_description)
    #validation 
    validation_res = evaluate_hallucinations_artworkinfo(artwork.get("text"), artwork_info)
    print(f'validation result:{validation_res}')
    clean_artwork_info = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', artwork_info) 
    voice_artwork = await converter_text_to_voice(clean_artwork_info)
    max_caption_length = 1024

    image_url = artwork.get("image")
    send_images = context.user_data.get('send_images', False)

    if send_images and image_url:
        if len(artwork_info) <= max_caption_length:
            await query.message.reply_photo(image_url, caption=artwork_info)
        else:
            await query.message.reply_photo(image_url, caption=artwork_info[:max_caption_length])
            await send_text_in_chunks(artwork_info[max_caption_length:], lambda text: query.message.reply_text(text, parse_mode="Markdown"))
    else:
        await send_text_in_chunks(artwork_info, lambda text: query.message.reply_text(text, parse_mode="Markdown"))

    await query.message.reply_voice(voice_artwork)

    context.user_data['current_artwork_index'] += 1

    if context.user_data['current_artwork_index'] < len(context.user_data['artworks']):
        keyboard = [[InlineKeyboardButton("Следующий экспонат", callback_data='next_artwork')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Задайте вопрос о текущем экспонате или нажмите ниже, чтобы перейти к следующему.",
            reply_markup=reply_markup
        )
    else:
        keyboard = [[InlineKeyboardButton("Завершить маршрут", callback_data='end_tour')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Задайте вопрос о текущем экспонате. Это последний экспонат нашего маршрута!",
            reply_markup=reply_markup
        )

async def end_tour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_description = context.user_data.get('user_description', '')
    await query.message.reply_text(generate_goodbye_word(exhibition_description, user_description))

def main():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Старт$"), start))
    app.add_handler(CallbackQueryHandler(handle_choice, pattern='^(with_images|without_images)$'))
    app.add_handler(CallbackQueryHandler(handle_tour_length, pattern='^(short|medium|long)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    app.add_handler(CallbackQueryHandler(next_artwork, pattern='next_artwork'))
    app.add_handler(CallbackQueryHandler(end_tour, pattern='end_tour'))

    print("Museum Guide Bot is running!")
    app.run_polling()

if __name__ == '__main__':
    main()