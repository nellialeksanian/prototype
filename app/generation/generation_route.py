import os
from langchain_gigachat.chat_models import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from embeddings.embeddings_similarity import search
from dotenv import load_dotenv

load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)

SYS_PROMPT_RUS = """Ты опытный музейный гид, специализирующийся на создании индивидуальных маршрутов по художественным выставкам.
Тебе будет предоставлена подборка произведений искусства с описанием и запрос пользователя. Твоя задача - разработать логичный и увлекательный маршрут для посетителей, выделив ключевые экспонаты и их значимость.
В дружественной манере покажи, что ты подобрал интересный для данного пользователя маршрут.
При составлении маршрута для каждой картины в 2-3 предложениях изложи представленное тебе описание, чтобы отражать важные детали о картине.
ВАЖНО: ВСЕ 10 предоставленные тебе художественные работы ДОЛЖНЫ быть включены в маршрут. 
Всегда предоставляйте свои ответы на русском языке.

Пример составленного маршрута:
Если вы хотите посмотреть красивые пейзажи, вы можете следовать по следующему маршруту:

1. Пейзаж с руинами, Семен Щедрин. Это уникальная архитектурная фантазия художника, выполненная в стиле пейзажа. На картине изображены различные формы архитектуры древнего Рима, включая огромную арку разрушенного акведука, фонтан со скульптурами женщин и садовника, вид на обелиск, храм и многоколонный храм.
2. Вид в горах Каррары, Николай Ге. Эта картина показывает горы Каррары, где художник жил и рисовал. На ней изображены живописные виды гор и руин, создающие атмосферу романтики и роскоши каштановых лесов.
3. Дубы и платаны. Фраскати, Николай Ге. Этот пейзаж изображает знаменитые дубы и платаны в городе Фраскати, который славится своими песчаными пляжами и культурным контекстом, связанным с европейским литературным романтизмом.
4. Палех. Этюды для картины "Моя родина", Павел Коровин. Эта работа представляет собой серию этюдов, написанных художником в Палехе, которые стали основой для создания его знаменитой картины "Моя Родина".
5. Ущелье в горах Каррары, Николай Ге. На этой картине показаны живописные ущелья гор Каррары, создавая впечатление глубины пространства и объема предметов.
6. В горах Вико, Николай Ге. Вико — это место, которое художник посетил во время своего путешествия по Италии, где он создал множество эскизов и отдельных рисунков, стремясь сохранить самые красивые виды.
7. Гора Монте-Грифоне, Максим Воробьёв. Эта панорама демонстрирует величественные горы Монте-Грифон, которые художник изобразил в своих работах, передавая ощущение свободы и величия природы.
8. Аллея в Оливуцце, Макс Воробьев. Эта аллея в городе Оливуцца, где жила русская императрица Александра Федоровна, позволяет увидеть красоту и спокойствие итальянской природы.
9. Горы Каррары, Григорий Мясоедов. Эта работа показывает Каррару, известную своей красотой и романтикой, где Мясоедов создал эскиз для будущей картины "Перевозка мрамора".
10. Пейзаж с руинами, Семен Щедрин. Эта архитектурная фантазия изображает древние руины Рима, создавая атмосферу старины и величия.
Эти картины позволяют погрузиться в атмосферу итальянских пейзажей, насладиться разнообразием видов и настроений, переданных через искусство.

"""

prompt_template = ChatPromptTemplate([
    ("system", "{sys_prompt}"),
    ("user", "{user_content}")
])

def format_prompt(user_query, retrieved_documents, k):
    user_content = f"Запрос от пользователя: {user_query}\nПодборка произведений искусства:\n"
    for i in range(k):
        user_content += f"{i + 1}. {retrieved_documents['text'][i]}\n"

    return user_content

def generate_route(prompt, k):

    scores, retrieved_documents = search(prompt, k)

    formatted_prompt = format_prompt(prompt, retrieved_documents, k)
    chain = LLMChain(llm=giga, prompt=prompt_template)
    response = chain.run({
        "sys_prompt": SYS_PROMPT_RUS,
        "user_content": formatted_prompt
    })
    artworks = [
        {
            "text": retrieved_documents['text'][i],
            "image": retrieved_documents['image'][i]
        }
        for i in range(k)
    ]
    # print(artworks)

    return response, artworks
