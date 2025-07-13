import uuid
import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import or_f
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import (ReplyKeyboardMarkup, Message, CallbackQuery, FSInputFile, KeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import re
import logging

import settings.settings
from sql.create_tables import init_db_pool, close_db_pool, save_session_info_to_database, save_generated_answer_to_database, save_generated_artwork_info_to_database, save_generated_goodbye_to_database, save_generated_route_to_database
from generation.generate_voice import converter_text_to_voice
from generation.generation_route import route_builder
from generation.generate_artwork_info import generate_artwork_info, generate_artwork_info_max
from generation.generate_answer import generate_answer, generate_answer_max
from process_data.load_data import send_images_then_text_group, send_text_in_chunks
from validation.validation_QA import evaluate_hallucinations
from validation.validation_artworkinfo import evaluate_hallucinations_artworkinfo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

pool = None
TOKEN = settings.settings.TELEGRAM_TOKEN

class TourState(StatesGroup):
    awaiting_description = State()
    awaiting_format = State()
    awaiting_tour_length = State()
    route_mode = State()
    question_mode = State()

bot = Bot(token=TOKEN)
dp = Dispatcher()

def create_keyboard(buttons):
    keyboard = InlineKeyboardBuilder()
    for text, data in buttons:
        keyboard.button(text=text, callback_data=data)
    return keyboard.as_markup()

permanent_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать заново")],
        [KeyboardButton(text="Завершить экскурсию")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)
@dp.message(or_f(
    F.text == "/start",
    F.text.lower() == "начать заново"
))
async def start(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    session_id = str(uuid.uuid4())

    await save_session_info_to_database(session_id, user_id, username)
    await state.set_state(TourState.awaiting_description)
    await state.update_data(
        state='route_mode',
        current_artwork_index=0,
        session_id=session_id,
        user_id=user_id
    )

    await message.answer(
        "Давай познакомимся:\n"
        "🧠 Сколько тебе лет?\n"
        "🎨 Чем ты увлекаешься?\n"
        "💡 Что привело тебя сюда: учеба, вдохновение или просто любопытство?\n\n"
        "*Напиши* в ответ немного о себе — это поможет мне составить маршрут, который подойдёт именно тебе 😊",
        parse_mode=ParseMode.MARKDOWN
    )

    await message.answer(
        "Если в любой момент захочешь выйти или начать заново — нажми кнопку внизу 👇",
        reply_markup=permanent_keyboard
    )

@dp.message(TourState.awaiting_description)
async def handle_description(message: Message, state: FSMContext):
    if message.text == "Завершить экскурсию":
        await end_tour_handler(message, state)
        return  
    await state.update_data(user_description=message.text)
    await state.set_state(TourState.awaiting_format)
    keyboard = create_keyboard([
        ("С изображением", "with_images"),
        ("Без изображения", "without_images")
    ])
    await message.answer(
        "Я очень рад с вами познакомиться!🙌\n"
        "\n"
        "Какой формат тебе удобен?",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.in_("with_images without_images".split()))
async def handle_format(query: CallbackQuery, state: FSMContext):
    await state.update_data(send_images=query.data == "with_images")
    await query.answer()
    await state.set_state(TourState.awaiting_tour_length)
    keyboard = create_keyboard([
        ("🕒 Экспресс", "short"),
        ("⏳ Стандарт", "medium"),
        ("🕰 Полное погружение", "long")
    ])
    await query.message.answer("Выберите продолжительность маршрута:", reply_markup=keyboard)

@dp.callback_query(F.data.in_(["short", "medium", "long"]))
async def handle_tour_length(callback: CallbackQuery, state: FSMContext):
    tour_lengths = {
        "short": random.randint(5, 9),
        "medium": random.randint(10, 18),
        "long": random.randint(19, 27)
    }

    top_k = tour_lengths.get(callback.data, 5)
    await state.update_data(top_k=top_k)
    await state.set_state(TourState.route_mode)

    await callback.answer()
    answer = """А теперь расскажи, что тебе интересно посмотреть.\n\nТы можешь просто описать тему, настроение или даже конкретные типы работ, которые хочешь увидеть (например, *яркие картины*, *что-то про природу*, *современное искусство*).\n\n📌 Чем точнее ты сформулируешь интерес — тем точнее будет маршрут!"""
    await callback.message.answer(answer, parse_mode=ParseMode.MARKDOWN)

@dp.message(TourState.route_mode)
async def generate_route_response(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    if message.text == "Завершить экскурсию":
        await end_tour_handler(message, state)
        return  
    await message.answer("Подождите немного, я готовлю ваш маршрут... ⏳")
    await asyncio.sleep(0)

    try:
        user_query = message.text
        user_description = data.get('user_description', '')
        top_k = data.get("top_k", 5)
        logging.info(f"top_k: {top_k}")
        route, artworks, output_image_path = await route_builder.generate_route(k=top_k, user_description=user_description, user_query=user_query)
        
        try:
            await message.bot.unpin_chat_message(chat_id=message.chat.id)
        except Exception as e:
            print(f"Не удалось открепить: {e}")

        try:
            photo = FSInputFile(output_image_path) 
            caption = """*Карта вашего маршрута*\n\n Начало маршрута — точка «0» (вход на выставку).\n\n Вы пройдёте по круговому маршруту и завершите его в той же точке.\n\n 🟣 Фиолетовые экспонаты — те, которые вы увидите во время персональной экскурсии. Номера рядом соответствуют списку выше.\n\n ⚪ Серые экспонаты — это просто ориентиры. Вы пройдёте мимо них по пути к основным точкам.\n\n 📍Чтобы снова открыть карту, нажмите на закреплённое сообщение.\n\n Чтобы продолжить маршрут, нажмите на *круглую кнопку-стрелку в правом нижнем углу* — она пролистает вас дальше  ➡️."""
            await message.answer(route)
            sent = await message.answer_photo(photo, caption=caption, parse_mode=ParseMode.MARKDOWN)
            await message.bot.pin_chat_message(
            chat_id=message.chat.id,
            message_id=sent.message_id,
            disable_notification=True
        )
            if os.path.exists(output_image_path):
                os.remove(output_image_path)
        except Exception as e:
            logging.error(f"Error with sending photo: {e}")

        titles = [artwork.get('name') for artwork in artworks]
        await state.update_data(artworks=artworks) 
        await save_generated_route_to_database(session_id, user_description, user_query, top_k, titles, route)
        await message.answer("🎧 Экскурсия содержит аудио, которое рекомендуется слушать на *1,5x* — так привычнее для слуха!", parse_mode=ParseMode.MARKDOWN) 
        await message.answer("Вы готовы начать экскурсию?", reply_markup=create_keyboard([("Да, я готов(а)", "next_artwork")]))
    except Exception as e:
        logging.error(f"Route generation error: {e}")
        await message.answer("Возникла ошибка, возможно ваш запрос оказался слишком сложным для меня")
        await state.set_state(TourState.route_mode)
        await message.answer("Давайте попробуем снова! Пожалуйста, уточните свои предпочтения, и мы перегенерируем маршрут. ⏳")

@dp.callback_query(F.data == "next_artwork")
async def handle_next_artwork(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    await state.set_state(TourState.question_mode)
    current_artwork_index = data.get('current_artwork_index', 0)
    artworks = data.get('artworks', [])
    
    artwork = artworks[current_artwork_index]
    title = artwork.get('name', '')
    await state.update_data(state='question_mode', last_shown_artwork_index=current_artwork_index)
    
    await query.answer()
    user_description = data.get('user_description', '')
    await query.message.answer("Обрабатываю описание экспоната... Подождите немного! ⏳")
    await asyncio.sleep(0)

    asyncio.create_task(process_artwork_info(query, state, data, artwork, user_description, session_id, title))
    
async def process_artwork_info(query: CallbackQuery, state: FSMContext, data, artwork, user_description, session_id, title):
    try:
        artwork_info, generation_time_text = await generate_artwork_info(artwork, user_description)
        logging.info(f"Generated artwork info: {artwork_info[:100]}...")

        try:
            validation_res = await evaluate_hallucinations_artworkinfo(session_id, artwork, artwork_info)
            logging.info(f'validation result:{validation_res}')
        except Exception as e:
            validation_res = 'No validation '
            logging.error(f"Error while validation: {e}")
        
        if validation_res.lower() == "hallucinated":
            artwork_info, generation_time_text = await generate_artwork_info_max(artwork, user_description)
            validation_res_max = await evaluate_hallucinations_artworkinfo(session_id, artwork, artwork_info)
            if validation_res_max.lower() == "hallucinated":
                artwork_info = artwork.get("short_description")
        else:
            artwork_info = artwork_info
        clean_artwork_info = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', artwork_info)

        voice_artwork = None
        try:
            voice_artwork, generation_time_audio = await converter_text_to_voice(clean_artwork_info)
            voice_filename = voice_artwork.filename if voice_artwork else None
        except Exception as e:
            logging.error(f"Cannot send audio: {e}")
        

        send_images = data.get('send_images', False)
        image_urls = artwork.get("image")
        artwork_name = artwork.get("name")
        artwork_caption = artwork_name + '\n\n Экспонат на карте: ' + artwork.get("id")

        if send_images and image_urls:
            image_urls = [url.strip() for url in image_urls.split(';') if url.strip()]
            logging.info(f"Image URLs to send: {image_urls}")

            await send_images_then_text_group(
                artwork_caption,
                artwork_info,
                image_urls,
                lambda text: query.message.answer(text, parse_mode=ParseMode.MARKDOWN),
                bot,
                query.message.chat.id
            )
        else:
            await send_text_in_chunks(artwork_info, lambda text: query.message.answer(text, parse_mode=ParseMode.MARKDOWN))

        if voice_artwork:
            await query.message.answer_voice(voice_artwork)
        else:
            await query.message.answer("К сожалению, я не смог сгенерировать аудиоформат")


        await save_generated_artwork_info_to_database(session_id, user_description, title, artwork_info, voice_filename, generation_time_text, generation_time_audio)    
        await state.update_data(current_artwork_index=data.get('current_artwork_index', 0) + 1)

        # Check if more artworks exist
        current_artwork_index_check = data.get('current_artwork_index', 0) + 1
        artworks = data.get('artworks', [])
        if current_artwork_index_check < len(artworks):
            keyboard = create_keyboard([("Следующий экспонат", "next_artwork")])
            await query.message.answer(
                "Задайте вопрос о текущем экспонате или нажмите ниже, чтобы перейти к следующему.",
                reply_markup=keyboard
            )
        else:
            keyboard = create_keyboard([("Завершить маршрут", "end_tour")])
            await query.message.answer(
                "Задайте вопрос о текущем экспонате. Это последний экспонат нашего маршрута!",
                reply_markup=keyboard
            )
    except Exception as e:
        logging.error(f"Error in process_artwork_info: {e}")

@dp.message(TourState.question_mode)
async def process_question(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    current_artwork_index = data.get("current_artwork_index", 0)
    if message.text == "Завершить экскурсию":
        await end_tour_handler(message, state)
        return  
    user_question = message.text
    artwork = data.get("artworks", [])[data.get("last_shown_artwork_index", 0)]
    title = artwork.get('name', '')

    await message.answer("Обрабатываю ваш вопрос... Подождите немного! ⏳")
    await asyncio.sleep(0)

    asyncio.create_task(handle_question_background(message, state, data, session_id, user_question, artwork, title, current_artwork_index))

async def handle_question_background(message: Message, state: FSMContext, data: dict, session_id: str, user_question: str, artwork: dict, title: str, current_artwork_index: int):
    user_description = data.get("user_description")
    answer, generation_time_text = await generate_answer(user_question, artwork, user_description)
    try:
        validation_res = await evaluate_hallucinations(session_id, artwork, answer, user_question)
        logging.info(f'validation result:{ validation_res}')
    except Exception as e:
        validation_res = 'No validation'
        logging.error(f"Error while validation: {e}")
    
    if validation_res.lower() == "false":
        clean_answer = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', answer)
        
        try:
            voice_answer, generation_time_audio = await converter_text_to_voice(clean_answer)
            voice_filename = voice_answer.filename if voice_answer else None 
        except Exception as e:
            logging.error(f"Cannot send audio: {e}")

        await message.answer(answer, parse_mode=ParseMode.MARKDOWN)
        if voice_answer:
            await message.answer_voice(voice_answer)
        else:
            await message.answer("К сожалению, я не смог сгенерировать аудиофрмат.")
        await save_generated_answer_to_database(session_id, user_question, user_description, title, clean_answer, voice_filename, generation_time_text, generation_time_audio)
    else:
        answer_max, generation_time_text = await generate_answer_max(user_question, artwork, user_description)
        secondary_validation_res = await evaluate_hallucinations(session_id, artwork, answer_max, user_question)
        if secondary_validation_res.lower() == "false":
            await message.answer(answer_max)
            clean_answer_max = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', answer_max)
            try:
                voice_answer_max, generation_time_audio = await converter_text_to_voice(clean_answer_max)
                voice_filename_max = voice_answer_max.filename if voice_answer_max else None 
            except Exception as e:
                logging.error(f"Cannot send audio: {e}")
                
            if voice_answer_max:
                await message.answer_voice(voice_answer_max)
            else:
                await message.answer("К сожалению, я не смог сгенерировать аудиофрмат.")
            await save_generated_answer_to_database(session_id, user_question, user_description, title, clean_answer_max, voice_filename_max, generation_time_text, generation_time_audio)
        else:
            answer = "К сожалению, я затрудняюсь ответить. Пожалуйста, переформулируйте ваш вопрос."
            await message.answer(answer)
            await save_generated_answer_to_database(session_id, user_question, user_description, title, answer, None, None, None)


    if current_artwork_index < len(data.get("artworks")):
        keyboard = create_keyboard([("Следующий экспонат", "next_artwork")])
        await message.answer("Задайте вопрос о текущем экспонате или нажмите ниже, чтобы перейти к следующему.", reply_markup=keyboard)
    else:
        keyboard = create_keyboard([("Завершить маршрут", "end_tour")])
        await message.answer("Задайте вопрос о текущем экспонате. Это последний экспонат нашего маршрута!", reply_markup=keyboard)

@dp.message(F.text == "Завершить экскурсию")
@dp.callback_query(F.data == "end_tour")
async def end_tour_handler(message_or_query, state: FSMContext):
    feedback_form = (
        "🎨 Благодарим за участие в выставке «Культурный слой» в музеи имени И. Я. Словцова. Это был увлекательный путь через историю и культуру Тюмени, представленные через призму современного искусства.\n\n"
        "🌐 Хочешь продолжить знакомство с музеем? Загляни на [сайт](https://museum72.ru/afisha/glavnyy-kompleks-imeni-i-ya-slovtsova/muzeynyy-kompleks-imeni-i-ya-slovtsova/kulturnyy-sloy/)\n\n"
        "📝 Нам важно услышать, как всё прошло. Пара минут — и ты поможешь сделать проект лучше:\n\n"
        "[Оценить экскурсию и поделиться мнением](https://docs.google.com/forms/d/e/1FAIpQLSfBvOxkqVCbAktduDqEtY82-BJcQw8g4H18GTz_gurAKT-74A/viewform)\n\n"
        "До новых встреч в мире искусства! 🎭"
    )
    if isinstance(message_or_query, Message):
        data = await state.get_data()
        message = message_or_query
        await message.answer(feedback_form, parse_mode=ParseMode.MARKDOWN)
    else:
        data = await state.get_data()
        query = message_or_query
        await query.message.answer(feedback_form, parse_mode=ParseMode.MARKDOWN)
    await state.clear()

# Comment out the function below if it causes bugs
@dp.error()
async def error_handler(update, exception: Exception = None):
    if isinstance(exception, TelegramNetworkError):
        logging.error(f"Network error while processing update: {exception}")

        try:
            if isinstance(update, types.CallbackQuery):
                await update.answer("Пожалуйста, нажмите на кнопку ещё раз", show_alert=True)
            elif isinstance(update, types.Message):
                await update.answer("Пожалуйста, нажмите на кнопку ещё раз")
        except Exception as e:
            logging.error(f"Error while sending a message to user: {e}")
        
        return True

    return False

async def main():
    await init_db_pool()
    await dp.start_polling(bot)
    await dp.start_polling(bot, on_shutdown=close_db_pool)

if __name__ == '__main__':
    asyncio.run(main())
