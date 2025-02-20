import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from process_data.load_data import clean_text
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """Я хочу, чтобы ты общался с пользователем, учитывая его описание: {user_description}. Ты — музейный гид, создающий персонализированные описания экспонатов на основе интересов пользователя: {user_description}. Твоя цель — представить информацию о картинах увлекательно и понятно, подчеркивая детали, которые могут заинтересовать пользователя. Информация о картине должна быть логично встроена в маршрут экспонатов, где каждый новый объект — это продолжение пути.

Предоставь краткое описание картины, избегая длинных вводных фраз, чтобы текст был легким для восприятия. Можно использовать списки, но каждый элемент с новой строки.

Информация о картине: {artwork}
"""



giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

def generate_artwork_info(artwork, user_description):
    response =  llm_chain.invoke({ "artwork": artwork, "user_description": user_description})
    response_text = response.content
    print('1 попытка создать описание:', response)

    if len(response_text) < 550:
        print("Модель отказалась генерировать ответ. Попробуем перегенерировать...")
        response =  llm_chain.invoke({ "artwork": artwork, "user_description": None})
        print('2 попытка создать описание:', response)

    response_text_new = response.content
    if len(response_text_new) < 550:
        print("Модель отказалась генерировать ответ. Попробуем отправить описание...")
        response =  clean_text(artwork)
        print('3 попытка создать описание:', response)


    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)