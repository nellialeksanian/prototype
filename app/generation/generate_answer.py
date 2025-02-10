import os
import httpx
from langchain.prompts import PromptTemplate

from dotenv import load_dotenv

load_dotenv()

template_info = """Ты опытный музейный гид, специализирующийся на создании индивидуальных маршрутов по художественным выставкам.
Тебе будет предоставлено описание картины. Отвечай на вопросы пользователя исходя из данного описания
Вопрос от пользователя: {user_question}
Описание картины: {artwork}
"""

api_url = os.getenv("GENERATIVE_ENDPOINT_URL")
def format_prompt(user_question, artwork):
    return template_info.format(user_question=user_question, artwork=artwork)

def generate_answer(user_question, artwork):
    formatted_prompt = format_prompt(user_question, artwork)
    try:
        response = httpx.post(
            url = api_url,
            json={
                "model": "t-pro-it-1.0",
                "messages": [{"role": "system", "content": formatted_prompt}]
            },
            timeout=None)

        response.raise_for_status()
        generated_text = response.get("choices", [{}])[0].get("message", {}).get("content", "Ошибка генерации текста.")
        
        return generated_text
    
    except httpx.RequestError as e:
        return f"Request Error: {e}"
    except httpx.HTTPStatusError as e:
        return f"HTTP Error: {e}"
    except Exception as e:
        return f"Unexpected Error: {e}"
