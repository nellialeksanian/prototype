import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")
exhibition_description = os.getenv("EXHIBITION_DESCRIPTION")

template_info = """I want you to interact with the user based on their USER DESCRIPTION.  
    You are an experienced museum guide who has just led an interactive tour of the exhibition "Моя Третьяковка" at the Третьяковская галерея with given MUSEUM DESCRIPTION.  
    Write to the user informing them that the exhibition has concluded, thank them for choosing an AI guide, say a few words about the exhibition, and invite them to evaluate your work. Be sure to provide a link to the feedback form and upcoming events at the Museum Complex.   

   Instructions:
        - Respond in Russian language
        - !!! IMPORTANT: Use NO greetings such as "Привет" or "Здравствуйте" or any similar phrases. Respond only with the main content. !!!
        - The message should consist of 2-3 sentences, written in a style that matches the USER DESCRIPTION.  
        - This exhibition link MUST ALWAYS be sent: https://my.tretyakov.ru/app/gallery 
    
    USER DESCRIPTION:  
    =====  
    {user_description}  
    =====  

    MUSEUM DESCRIPTION:  
    =====  
    {info}  
    =====      

    Example message:  

        Благодарю вас за участие в экскурсии по выставке "Моя Третьяковка" в виртуальном музейном пространсве Третьяковская галерея! Мы надеемся, что наша прогулка по культуре и истории оставила у вас массу впечатлений.
        Если хотите поделиться мнением или оценить нашу работу, мы будем признательны за ваш отзыв: [ссылка на форму оценки].
        Продолжить знакомство с миром искусства вы моежет на сайте: https://my.tretyakov.ru/app/gallery 

"""  

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)        

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

def generate_goodbye_word(exhibition_description, user_description):
    parsed_unpack = open(exhibition_description, encoding="utf-8").read()
    print(f'Annotation: {parsed_unpack}')
    response =  llm_chain.invoke({"info": parsed_unpack, "user_description": user_description})
    print(response)
    if hasattr(response, 'content'):
        return response.content 
    else:
        return str(response)
