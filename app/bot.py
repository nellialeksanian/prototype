import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import (ReplyKeyboardMarkup, Message, CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import random
import re
import logging

from generation.generate_voice import converter_text_to_voice
from generation.generation_route import generate_route
from generation.generate_artwork_info import generate_artwork_info
from generation.generate_answer import generate_answer, generate_answer_max
from process_data.load_data import send_text_in_chunks, send_text_with_image
from generation.generate_goodbye_word import generate_goodbye_word, exhibition_description
from validation.validation_QA import evaluate_hallucinations
from validation.validation_artworkinfo import evaluate_hallucinations_artworkinfo

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

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

@dp.message(F.text == "/start")
@dp.message(F.text == "Старт")
async def start(message: Message, state: FSMContext):
    await state.set_state(TourState.awaiting_description)
    await state.update_data(state='route_mode', current_artwork_index=0)
    keyboard = ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="Старт")]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer(
                "Привет! 👋Я твой виртуальный гид по виртуальной выставке 'Моя Третьяковка'.\n"
        "\n"
        "Я создан на базе модели GigaChat — это значит, что я умею подстраиваться под твои интересы и вести настоящую живую беседу 🤖✨\n"
        "\n"
        "Давай немного познакомимся:\n"
        "🧠 Сколько тебе лет?\n"
        "🎨 Чем ты увлекаешься?\n"
        "💡 Что привело тебя сюда: учеба, вдохновение или просто любопытство?\n"
        "\n"
        "Напиши в ответ немного о себе — это поможет мне составить маршрут, который подойдёт именно тебе 😊", 
        reply_markup=keyboard
    )

@dp.message(TourState.awaiting_description)
async def handle_description(message: Message, state: FSMContext):
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
        "short": random.randint(4, 9),
        "medium": random.randint(10, 18),
        "long": random.randint(19, 27)
    }

    top_k = tour_lengths.get(callback.data, 5)
    await state.update_data(top_k=top_k)
    await state.set_state(TourState.route_mode)

    await callback.answer()
    await callback.message.answer(
        "А теперь расскажи, что тебе интересно посмотреть.\n"
        "Ты можешь просто описать тему, настроение или даже конкретные типы работ, которые хочешь увидеть (например, *яркие картины*, *что-то про природу*, *современное искусство*).\n"
        "\n"
        "📌 Чем точнее ты сформулируешь интерес — тем точнее будет маршрут!"
    )

@dp.message(TourState.route_mode)
async def generate_route_response(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("Подождите немного, я готовлю ваш маршрут... ⏳")
    user_query = message.text
    user_description = data.get('user_description', '')
    top_k = data.get("top_k", 5)
    logging.debug(f"top_k: {top_k}")
    route, artworks = generate_route(top_k, user_description, user_query)
    await state.update_data(artworks=artworks)

    clean_route_for_gen = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', route)
    clean_route = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,:"«»]', '', route)
    voice_route = await converter_text_to_voice(clean_route_for_gen)

    await send_text_in_chunks(clean_route, lambda text: message.answer(text, parse_mode=ParseMode.MARKDOWN))
    if voice_route:
        await message.answer_voice(voice_route)
    await message.answer("Вы готовы начать экскурсию?", reply_markup=create_keyboard([("Да, я готов(а)", "next_artwork")]))

@dp.callback_query(F.data == "next_artwork")
async def handle_next_artwork(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(TourState.question_mode)
    current_artwork_index = data.get('current_artwork_index', 0)
    artworks = data.get('artworks', [])
    
    artwork = artworks[current_artwork_index]
    await state.update_data(state='question_mode', last_shown_artwork_index=current_artwork_index)
    
    await query.answer()
    user_description = data.get('user_description', '')
    await query.message.answer("Обрабатываю ваш вопрос... Подождите немного! ⏳")
    
    artwork_info = generate_artwork_info(artwork.get("text"), user_description)
    validation_res = evaluate_hallucinations_artworkinfo(artwork.get("text"), artwork_info)
    logging.debug(f'validation result:{validation_res}')
    
    clean_artwork_info = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', artwork_info)
    voice_artwork = await converter_text_to_voice(clean_artwork_info)
    
    send_images = data.get('send_images', False)
    image_url = artwork.get("image")

    if send_images and image_url:
        await send_text_with_image(
            artwork_info, 
            image_url,
            lambda text: query.message.answer(text, parse_mode=ParseMode.MARKDOWN), 
            lambda url, caption: query.message.answer_photo(url, caption=caption)
        )
    else:
        await send_text_in_chunks(artwork_info, lambda text: query.message.answer(text, parse_mode=ParseMode.MARKDOWN))

    if voice_artwork:
        await query.message.answer_voice(voice_artwork)

    await state.update_data(current_artwork_index=current_artwork_index + 1)

    current_artwork_index_check = data.get('current_artwork_index', 0) + 1
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

@dp.message(TourState.question_mode)
async def process_question(message: Message, state: FSMContext):
    data = await state.get_data()
    user_question = message.text
    artwork = data.get("artworks", [])[data.get("last_shown_artwork_index", 0)]

    await message.answer("Обрабатываю ваш вопрос... Подождите немного! ⏳")
    
    answer = generate_answer(user_question, artwork, data.get("user_description"))
    validation_res = evaluate_hallucinations(artwork.get("text"), answer, user_question)
    logging.debug(f'validation result:{ validation_res}')
    
    if validation_res.lower() == "false":
        clean_answer = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', answer)
        voice_answer = await converter_text_to_voice(clean_answer)
        await message.answer(answer, parse_mode=ParseMode.MARKDOWN)
        if voice_answer:
            await message.answer_voice(voice_answer)
    else:
        answer_max = generate_answer_max(user_question, artwork, data.get("user_description"))
        secondary_validation_res = evaluate_hallucinations(artwork.get("text"), answer_max, user_question)
        if secondary_validation_res.lower() == "false":
            await message.answer(answer_max)
            clean_answer_max = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.,]', '', answer_max)
            voice_answer_max = await converter_text_to_voice(clean_answer_max)
            await message.answer_voice(voice_answer_max)
        else:
            await message.answer("К сожалению, я затрудняюсь ответить. Пожалуйста, переформулируйте ваш вопрос.")
    
    current_artwork_index = data.get("current_artwork_index", 0)
    if current_artwork_index < len(data.get("artworks")):
        keyboard = create_keyboard([("Следующий экспонат", "next_artwork")])
        await message.answer("Задайте вопрос о текущем экспонате или нажмите ниже, чтобы перейти к следующему.", reply_markup=keyboard)
    else:
        keyboard = create_keyboard([("Завершить маршрут", "end_tour")])
        await message.answer("Задайте вопрос о текущем экспонате. Это последний экспонат нашего маршрута!", reply_markup=keyboard)

@dp.callback_query(F.data == "end_tour")
async def end_tour(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await query.answer()
    goodbye_text = generate_goodbye_word(exhibition_description, data.get("user_description", ""))
    await query.message.answer(goodbye_text + f"\n\nПродолжить знакомство с миром искусства вы можете на сайте: https://my.tretyakov.ru/app/gallery")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())