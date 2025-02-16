import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """Я хочу, чтобы ты общался с пользователем, учитывая его описание: {user_description}. Ты — опытный и увлекательный музейный гид, специализирующийся на создании персонализированных описаний экспонатов художественных выставкок. Твоя задача — создать интересную и понятную информацию о картинах, основываясь на интересах пользователя, чтобы сделать описание каждого экспоната максимально увлекательным для него.

Тебе будет предоставлено описание картины. Используя информацию о пользователе, дай краткую и увлекательную информацию о картине, подчеркивая те детали, которые могут быть наиболее интересны этому конкретному пользователю. Важно, чтобы информация о картине была логично встроена в маршрут, где ты последовательно рассказываешь об экспонатах. Каждая картина — это часть маршрута, а ты гид, который сопровождает пользователя на всем пути.

!!! ВАЖНО: Категорически запрещено начинать ответ с приветствия, обращений типа "Здравствуйте", "Привет" или любых подобных фраз. Немедленно переходи к сути, без вводных слов.!!!

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
    response_text = str(response)
    print('Попытка 1:', response)

    if len(response_text) < 450:
        print("Модель отказалась генерировать ответ. Попробуем перегенерировать...")
        response =  llm_chain.invoke({ "artwork": artwork, "user_description": None})
        print('Попытка 2:', response)

    response_text_new = response.content
    response_text_new = str(response)
    if len(response_text_new) < 450:
        print("Модель отказалась генерировать ответ. Попробуем отправить описание...")
        response =  artwork
        print('Попытка 3:', response)


    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)