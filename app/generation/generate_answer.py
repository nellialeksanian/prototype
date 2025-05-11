import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import time
import settings.settings

gigachat_token = settings.settings.GIGACHAT_TOKEN
gigachat_token_max=settings.settings.GIGACHAT_TOKEN_MAX

giga = GigaChat (
    credentials=gigachat_token,
    model='GigaChat',
    verify_ssl_certs=False
)

giga_max = GigaChat (
    credentials=gigachat_token_max,
    model="GigaChat-Max", 
    verify_ssl_certs=False
)  

template_info = """You must communicate with the user based on their USER DESCRIPTION.  
Your task is to provide the most accurate and engaging response to the user's QUESTION, based on their interests to make the answer as captivating as possible.  
Answer the QUESTION using the provided ARTWORK INFO.  
   Instructions:
        - Respond in Russian language
        - If the QUESTION requires additional information that is not available in the current context, inform the user that you don't have enough data to provide a precise answer. 
        - !!! IMPORTANT: Use NO greetings such as "Привет" or "Здравствуйте" or any similar phrases. Respond only with the main content. !!!
        - Respond without repeating the artwork description. Use it only as a reference, and include parts of it in your reply ONLY if the user's question clearly requires it.
        - If the user simply expresses interest or emotions (e.g., “Мне очень нравится картина!”), respond briefly, as a guide would: acknowledge their interest with a warm comment or compliment.


        
    QUESTION:
    =====
    {user_question}
    =====

    USER DESCRIPTION:
    =====
    {user_description}
    =====

    ARTWORK INFO:
    =====
    {artwork}
    =====
"""

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga
llm_chain_max = prompt_info | giga_max

async def generate_answer(user_question, artwork, user_description):
    start_time_text = time.time()
    response =  await llm_chain.ainvoke({"user_question": user_question, "artwork": artwork, "user_description": user_description})
    response_text = response.content
    if len(response_text) < 350:
        response =  llm_chain.invoke({ "user_question": user_question, "artwork": artwork, "user_description": None})
    end_time_text = time.time()
    generation_time_text = float(end_time_text - start_time_text)
    if hasattr(response, 'content'):
        return response.content, generation_time_text
    else:
        return str(response), generation_time_text
    
async def generate_answer_max(user_question, artwork, user_description):
    start_time_text = time.time()
    response =  await llm_chain_max.ainvoke({"user_question": user_question, "artwork": artwork, "user_description": user_description})
    response_text = response.content
    if len(response_text) < 350:
        response =  llm_chain.invoke({ "user_question": user_question, "artwork": artwork, "user_description": None})
    end_time_text = time.time()
    generation_time_text = float(end_time_text - start_time_text)
    if hasattr(response, 'content'):
        return response.content, generation_time_text
    else:
        return str(response), generation_time_text