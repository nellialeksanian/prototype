from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import time
from process_data.load_data import clean_text
import settings.settings
from settings.retry_helpers import invoke_llm_chain

gigachat_token = settings.settings.GIGACHAT_TOKEN

giga = GigaChat (
    credentials=gigachat_token,
    model='GigaChat',
    scope="GIGACHAT_API_B2B",
    verify_ssl_certs=False
)

giga_max = GigaChat (
    credentials=gigachat_token,
    model="GigaChat-Max", 
    scope="GIGACHAT_API_B2B",
    verify_ssl_certs=False
)  

template_info = """You are a skilled museum guide specializing in personalized artwork descriptions. Make your explanations  appropriate for the user’s interests from their USER DESCRIPTION, making the information as captivating as possible.

    You will receive ARTWORK INFO. Provide a concise, engaging explanation, highlighting details that resonate most with this user.

    Instructions:
        - Respond in Russian language
        - Response consist of 4-5 sentences.
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

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga
llm_chain_max = prompt_info | giga_max

async def generate_artwork_info(artwork, user_description):
    start_time_text = time.time()
    response = await invoke_llm_chain(llm_chain, { "artwork": artwork.get('text'), "user_description": user_description})
    print(f'**Generation of the artwork_info with all parametrs.')
    finish_reason = response.response_metadata.get("finish_reason")


    if finish_reason == "blacklist":
        print(f"Finish reason for artwork_info: {finish_reason}. Regeneration with the short_description.")
        response =  await invoke_llm_chain(llm_chain, { "artwork": artwork.get('short_description'), "user_description": user_description})
        finish_reason = response.response_metadata.get("finish_reason")


    if finish_reason == "blacklist":
        print(f"Finish reason for artwork_info: {finish_reason}. Regeneration without user_description.")
        response =  await invoke_llm_chain(llm_chain,{ "artwork": artwork.get('short_description'), "user_description": None})
        finish_reason = response.response_metadata.get("finish_reason")


    if finish_reason == "blacklist":
        print(f"Finish reason for artwork_info: {finish_reason}. Send the origina artwork info.")
        response =  await clean_text(artwork.get('short_description'))

    end_time_text = time.time()
    generation_time_text = float(end_time_text - start_time_text)

    if hasattr(response, 'content'):
        return response.content, generation_time_text
    else:
        return str(response), generation_time_text

async def generate_artwork_info_max(artwork, user_description):
    start_time_text = time.time()
    response =  await invoke_llm_chain(llm_chain_max, { "artwork": artwork.get('text'), "user_description": user_description})
    finish_reason = response.response_metadata.get("finish_reason")
    print(f'**Generation of the artwork_info after validation with all parametrs.')

    if finish_reason == "blacklist":
        print(f"Finish reason for artwork_info after validation: {finish_reason}. Regeneration with the the short_description.")
        response = await invoke_llm_chain(llm_chain, { "artwork": artwork.get('short_description'), "user_description": user_description})
    
    if finish_reason == "blacklist":
        print(f"Finish reason for artwork_info after validation: {finish_reason}. Regeneration without user_description.")
        response =  await invoke_llm_chain(llm_chain,{ "artwork": artwork.get('short_description'), "user_description": None})
        finish_reason = response.response_metadata.get("finish_reason")

    if finish_reason == "blacklist":
        print(f"Finish reason for artwork_info after validation: {finish_reason}. Send the original artwork info.")
        response =  await clean_text(artwork.get('short_description'))

    end_time_text = time.time()
    generation_time_text = float(end_time_text - start_time_text)

    return response.content if hasattr(response, 'content') else str(response), generation_time_text