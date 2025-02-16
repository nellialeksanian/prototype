import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from tika import unpack

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")
exhibition_description = os.getenv('EXHIBITION_DESCRIPTION')

template_info =  """Я хочу, чтобы ты общался с пользователем, исходя из его описания: {user_description}. Ты — опытный музейный гид, который только что провел интерактивную экскурсию по выставке "Культурный слой" в Музейном комплексе имени И.Я. Словцова, описанной как: {info}. Напиши пользователю, что выставка завершена, поблагодари его за выбор ИИ-гида, скажи пару слов о выставке и пригласи оценить твою работу. Обязательно предоставь ссылку на форму оценки и на предстоящие мероприятия Музейного комплекса.
Сообщение должно состиять из 2-4 предложений, написанных в стиле, соответсвуеющем описанию пользователя.
Не забудь, что ссылка на выставку всегда должна быть отправлена в следующем виде:
{{https://museum72.ru/afisha/glavnyy-kompleks-imeni-i-ya-slovtsova/muzeynyy-kompleks-imeni-i-ya-slovtsova/kulturnyy-sloy/}}
Пример сообщения:
    Благодарю вас за участие в экскурсии по выставке "Культурный слой" в Музейном комплексе имени И.Я. Словцова! Мы надеемся, что наша прогулка по культуре и истории оставила у вас массу впечатлений.
   
    Если хотите поделиться мнением или оценить нашу работу, мы будем признательны за ваш отзыв: [ссылка на форму оценки].

    Не пропустите будущие выставки и мероприятия Музейного комплекса: https://museum72.ru/afisha/glavnyy-kompleks-imeni-i-ya-slovtsova/muzeynyy-kompleks-imeni-i-ya-slovtsova/kulturnyy-sloy/!
"""

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)        

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

def generate_goodbyu_word(exhibition_description, user_description):
    parsed_unpack = unpack.from_file(exhibition_description, requestOptions={'timeout': None})
    content = parsed_unpack['content']
    response =  llm_chain.invoke({"info": content, "user_description": user_description})
    if hasattr(response, 'content'):
        return response.content 
    else:
        return str(response)
