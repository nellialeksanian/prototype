import os
import httpx
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

template_info = """Ты опытный музейный гид, специализирующийся на создании индивидуальных маршрутов по художественным выставкам.
Тебе будет предоставлено описание картины. Дай пользователю краткую информацию о картине
информация о картине: {artwork}"""

api_url = os.getenv("GENERATIVE_ENDPOINT_URL")
model = "qwen"
prompt_info = PromptTemplate.from_template(template_info)
def generate_artwork_info(artwork):
    try:
        response = httpx.post(
            url = api_url,
            json={
                "model": "qwen",
                "messages": [{"role": "system", "content": template_info.format(artwork=artwork)}]
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
