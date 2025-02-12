import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """Ты опытный музейный гид, специализирующийся на создании индивидуальных маршрутов по художественным выставкам.
Тебе будет предоставлено описание картины. Отвечай на вопросы пользователя исходя из данного описания. Если вопрос требует дополнительной информации для ответа, которой нет в контексте, отвечай что у тб недостаточно информуции для ответа на вопрос.
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

def generate_answer(user_question, artwork):
    response =  llm_chain.invoke({"user_question": user_question, "artwork": artwork})
    # Access the content attribute if it exists
    if hasattr(response, 'content'):
        return response.content
    else:
        # Fallback: Convert to string if the expected attribute is not present
        return str(response)
    
def generate_answer_max(user_question, artwork):
    response =  llm_chain_max.invoke({"user_question": user_question, "artwork": artwork})
    # Access the content attribute if it exists
    if hasattr(response, 'content'):
        return response.content
    else:
        # Fallback: Convert to string if the expected attribute is not present
        return str(response)