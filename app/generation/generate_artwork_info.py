import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """Ты опытный музейный гид, специализирующийся на создании индивидуальных маршрутов по художественным выставкам.
Тебе будет предоставлено описание картины. Дай пользователю краткую информацию о картине
информация о картине: {artwork}"""

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

def generate_artwork_info(artwork):
    response =  llm_chain.invoke({"artwork": artwork})
    # Access the content attribute if it exists
    if hasattr(response, 'content'):
        return response.content
    else:
        # Fallback: Convert to string if the expected attribute is not present
        return str(response)
