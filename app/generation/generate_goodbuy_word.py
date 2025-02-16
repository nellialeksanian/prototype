import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from tika import unpack

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")
exhibition_description = os.getenv('EXHIBITION_DESCRIPTION')

template_info = """Ты опытный музейный гид, который только что провел интерактивную экскурсию для посетите музея Словцова по выставке 'Культурный слой' с таким описаниeм: {info}. Напиши пользователю, что выставка окончена в 1-2 предложениях. Сообщение должно включать ссылку на выставку: https://museum72.ru/afisha/glavnyy-kompleks-imeni-i-ya-slovtsova/muzeynyy-kompleks-imeni-i-ya-slovtsova/kulturnyy-sloy/ . В конце предложи оценить свою работу и дай ссылку на форму оценки. """
# template_info = """Ты опытный музейный гид, который только что провел интерактивную экскурсию для посетите музея Словцова по выставке 'Культурный слой' с таким описаниeм: {info}. Напиши пользователю, что выставка окончена, сделай это в стиле {user_description}. Сообщение должно включать ссылку на выставку: https://museum72.ru/afisha/glavnyy-kompleks-imeni-i-ya-slovtsova/muzeynyy-kompleks-imeni-i-ya-slovtsova/kulturnyy-sloy/ . В конце предложи оценить свою работу и дай ссылку на форму оценки. """

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

def generate_goodbuy_word(exhibition_description):
    parsed_unpack = unpack.from_file(exhibition_description, requestOptions={'timeout': None})
    content = parsed_unpack['content']
    response =  llm_chain.invoke({"info": content})
    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)

