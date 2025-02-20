import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """Я хочу, чтобы ты общался с пользователем, ориентируясь на его описание: {user_description}. Твоя задача — дать максимально точный и при этом увлекательный ответ на вопрос пользователя, основываясь на интересах пользователя, чтобы сделать ответ максимально увлекательным для него.
Тебе будет предоставлено описание картины. Отвечай на вопросы пользователя, опираясь на это описание. Если вопрос требует дополнительной информации, которой нет в текущем контексте, сообщи, что у тебя недостаточно информации для того, чтобы дать точный ответ.
Вопрос от пользователя: {user_question}
Описание картины: {artwork}
"""


giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)

giga_max = GigaChat(credentials=gigachat_token,
                model="GigaChat-Max", 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)


prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga
llm_chain_max = prompt_info | giga_max

def generate_answer(user_question, artwork, user_description):
    response =  llm_chain.invoke({"user_question": user_question, "artwork": artwork, "user_description": user_description})
    response_text = response.content
    if len(response_text) < 350:
        response =  llm_chain.invoke({ "user_question": user_question, "artwork": artwork, "user_description": None})
    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)
    
def generate_answer_max(user_question, artwork, user_description):
    response =  llm_chain_max.invoke({"user_question": user_question, "artwork": artwork, "user_description": user_description})
    response_text = response.content
    if len(response_text) < 350:
        response =  llm_chain.invoke({ "user_question": user_question, "artwork": artwork, "user_description": None})
    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)