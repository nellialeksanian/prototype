import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import time
from process_data.load_data import clean_text
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """You are a skilled museum guide specializing in personalized artwork descriptions. Make your explanations  appropriate for the user’s interests from their USER DESCRIPTION, making the information as captivating as possible.

    You will receive ARTWORK INFO. Provide a concise, engaging explanation, highlighting details that resonate most with this user.

    Instructions:
        - Respond in Russian language
        - Response consist of 4-5 sentences.
        - ALWAYS begin your response with the author's name and the title of the artwork.
        - Split the text into readable paragraphs to make it easier to perceive.
        - Each painting is part of a sequential tour, and you guide the user through the journey. Ensure the artwork information flows logically within the tour’s narrative.
        - !!! IMPORTANT: Use NO greetings such as "Привет" or "Здравствуйте" or any similar phrases. Respond only with the main content. !!!

    USER DESCRIPTION:
    =====
    {user_description}
    =====

    ARTWORK INFO:
    =====
    {artwork}
    =====


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


def generate_artwork_info(artwork, user_description):
    start_time_text = time.time()
    response =  llm_chain.invoke({ "artwork": artwork, "user_description": user_description})
    response_text = response.content
    print(f'**Generation of the artwork_info with all parametrs.')

    if len(response_text) < 450:
        print("The BLACKLIST problem. Regeneration with the less number of the parametrs.")
        response =  llm_chain.invoke({ "artwork": artwork, "user_description": None})
        print(f'**Generation of the artwork info without user_description.')

    response_text_new = response.content
    if len(response_text_new) < 450:
        print("The BLACKLIST problem. Send the origina artwork info.")
        response =  clean_text(artwork)
        print(f'**Responce is the original artwork info')

    end_time_text = time.time()
    generation_time_text = float(end_time_text - start_time_text)

    if hasattr(response, 'content'):
        return response.content, generation_time_text
    else:
        return str(response), generation_time_text


def generate_artwork_info_max(artwork, user_description):
    start_time_text = time.time()
    response =  llm_chain_max.invoke({ "artwork": artwork, "user_description": user_description})
    response_text = response.content
    print(f'**Generation of the artwork_info with all parametrs.')

    if len(response_text) < 450:
        print("The BLACKLIST problem. Regeneration with the less number of the parametrs.")
        response =  llm_chain.invoke({ "artwork": artwork, "user_description": None})
        print(f'**Generation of the artwork info without user_description.')

    response_text_new = response.content
    if len(response_text_new) < 450:
        print("The BLACKLIST problem. Send the origina artwork info.")
        response =  clean_text(artwork)
        print(f'**Responce is the original artwork info')

    end_time_text = time.time()
    generation_time_text = float(end_time_text - start_time_text)

    return response.content if hasattr(response, 'content') else str(response), generation_time_text