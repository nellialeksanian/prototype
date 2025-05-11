import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import time
import settings.settings

gigachat_token = settings.settings.GIGACHAT_TOKEN
print(gigachat_token)
exhibition_description = settings.settings.EXHIBITION_DESCRIPTION

giga = GigaChat(
    credentials=gigachat_token,
    model='GigaChat', 
    verify_ssl_certs=False
)        

template_info = """I want you to interact with the user based on their USER DESCRIPTION.  
    You are an experienced museum guide who has just led an interactive tour of the exhibition "Культурный слой" at the Музейный комплекс имени И.Я. Словцова with givven MUSEUM DESCRIPTION.  
    Write to the user informing them that the exhibition has concluded, thank them for choosing an AI guide, say a few words about the exhibition.   

   Instructions:
        - Respond in Russian language
        - !!! IMPORTANT: Use NO greetings such as "Привет" or "Здравствуйте" or any similar phrases. Respond only with the main content. !!!
        - The message should consist of 2-3 sentences, written in a style that matches the USER DESCRIPTION. 
    
    USER DESCRIPTION:  
    =====  
    {user_description}  
    =====  

    MUSEUM DESCRIPTION:  
    =====  
    {info}  
    =====      

    Example message:  

        Благодарю вас за участие в экскурсии по выставке "Культурный слой" в Музейном комплексе имени И.Я. Словцова! Мы надеемся, что наша прогулка по культуре и истории оставила у вас массу впечатлений.
"""  

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

async def generate_goodbye_word(exhibition_description, user_description):
    start_time_text = time.time()
    parsed_unpack = open(exhibition_description, encoding="utf-8").read()
    response =  await llm_chain.ainvoke({"info": parsed_unpack, "user_description": user_description})
    end_time_text = time.time()
    generation_time_text = float(end_time_text - start_time_text)
    return response.content if hasattr(response, 'content') else str(response), generation_time_text
