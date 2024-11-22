import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """Ты опытный музейный гид, специализирующийся на создании индивидуальных маршрутов по художественным выставкам.
Тебе будет предоставлено описание картины. Отвечай на вопросы пользователя исходя из данного описания
Вопрос от пользователя: {user_question}
Описание картины: {artwork}
"""

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', verify_ssl_certs=False)

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

def generate_answer(user_question, artwork):
    response =  llm_chain.invoke({"user_question": user_question, "artwork": artwork})
    # Access the content attribute if it exists
    if hasattr(response, 'content'):
        return response.content
    else:
        # Fallback: Convert to string if the expected attribute is not present
        return str(response)