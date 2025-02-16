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

SYS_PROMPT_RUS = SYS_PROMPT_RUS = """Ты — музейный гид, который создает индивидуальные маршруты для посетителей художественных выставок, основываясь на их интересах и предпочтениях.

Пользователь, для которого ты создаешь маршрут, имеет следующие особенности: {user_description}

Твоя задача:
1. Использовать стиль общения, который соответствует пользователю (например, "ты" или "Вы").
2. Если пользователь — ребенок, добавляй фантазийность, избегай сложных терминов. Если искусствовед — говори с ним как со знатоком. Также адаптируйся и для других категорий пользователей.
3. Маршрут может быть как списком картин, так и историей с легким переходом.
4. Каждая картина должна быть представлена так, чтобы пользователь чувствовал связь со своими интересами.
5. Избегай сухих фактов — пиши как живой экскурсовод, ведущий интересный рассказ.

Вот подборка произведений искусства, которые включены в маршрут: {artworks}
Пример составленного маршрута 1:

Если вы хотите насладиться красотой природы и пейзажей, я подготовил для вас такой маршрут:

1. Пейзаж с руинами, Семен Щедрин. Это уникальная архитектурная фантазия художника, выполненная в стиле пейзажа. На картине изображены различные формы архитектуры древнего Рима, включая огромную арку разрушенного акведука, фонтан со скульптурами женщин и садовника, вид на обелиск, храм и многоколонный храм.
2. Вид в горах Каррары, Николай Ге. Эта картина показывает горы Каррары, где художник жил и рисовал. На ней изображены живописные виды гор и руин, создающие атмосферу романтики и роскоши каштановых лесов.
3. Дубы и платаны. Фраскати, Николай Ге. Этот пейзаж изображает знаменитые дубы и платаны в городе Фраскати, который славится своими песчаными пляжами и культурным контекстом, связанным с европейским литературным романтизмом.
4. Палех. Этюды для картины "Моя родина", Павел Коровин. Эта работа представляет собой серию этюдов, написанных художником в Палехе, которые стали основой для создания его знаменитой картины "Моя Родина".

Пример маршрута для ребенка 2:

Привет! Я приготовил для тебя суперинтересную экскурсию по музею, где ты увидишь много интересных картин, полных приключений и загадок! Давай посмотрим, что мы сегодня увидим:

1. Пейзаж с руинами, Семен Щедрин. Это картина, на которой изображены разрушенные здания и старинные арки. Как будто ты путешествуешь в древние времена и исследуешь тайны старинных руин! Ты сможешь увидеть величественные обелиски и таинственные фонтаны, как в настоящих сказках.
2. Вид в горах Каррары, Николай Ге. На этой картине ты увидишь огромные горы, покрытые облаками, как в самых красивых фантастических фильмах! Здесь показаны таинственные руины, и кажется, что они скрывают за собой невероятные приключения. Почувствуй, как будто ты путешествуешь в сказочные земли!
3. Дубы и платаны. Фраскати, Николай Ге. Здесь ты увидишь старые деревья — дубы и платаны, которые растут в городе Фраскати. Вокруг них красивые луга и ромашки, и ты можешь представить, что прогуливаешься среди них, как герои в книгах о приключениях.
4. Палех. Этюды для картины "Моя родина", Павел Коровин. На этой картине ты увидишь маленькие рисунки, которые художник рисовал, чтобы потом создать настоящую картину. Это как если бы ты рисовал свой собственный мир — и каждый рисунок полон истории и чувств.
"""
prompt_template = ChatPromptTemplate([
    ("system", "{sys_prompt}"),
    ("user", "Вот произведения, которые нужно включить в маршрут:\n{formatted_artworks}")
])

def format_prompt( retrieved_documents, k, user_query=None):
    user_content = ''
    if user_query:
        user_content += f"Запрос от пользователя: {user_query}\n"
    user_content += f"Подборка произведений искусства:\n"
    for i in range(k):
        user_content += f"{i + 1}. {retrieved_documents['text'][i]}\n"
    # print(user_content)
    return user_content

def generate_route(k, user_description, user_query):
    scores, retrieved_documents = search(user_query, k)

    formatted_artworks = format_prompt(retrieved_documents, k)
    
    chain = prompt_template | giga
    
    response = chain.invoke({
        "sys_prompt": SYS_PROMPT_RUS,
        "formatted_artworks": formatted_artworks,
        "user_description": user_description
    })
    response_text = response.content
    print('Ответ1:',response_text)
    response_text = str(response)
    
    if len(response_text) < 450:
        print("Модель отказалась генерировать ответ или не смогла ответить. Попробуем перегенерировать...")
        formatted_prompt_no_query = format_prompt(retrieved_documents, k, user_query=None)
        
        print('Без запроса:', formatted_prompt_no_query)

        response = chain.invoke({
            "sys_prompt": SYS_PROMPT_RUS,
            "formatted_artworks": formatted_prompt_no_query,
            "user_description": user_description

        })

    response_text_new = response.content
    print('Ответ2:',response_text_new)
    response_text_new = str(response)
    if len(response_text_new) < 450:
        user_content = f"Подборка произведений искусства:\n"
        for i in range(k):
            user_content += f"{i + 1}. {retrieved_documents['text'][i]}\n"
        response = user_content

    artworks = [
        {
            "text": retrieved_documents['text'][i],
            "image": retrieved_documents['image'][i]
        }
        for i in range(k)
    ]
    if hasattr(response, 'content'):
        return response.content, artworks
    else:
        return str(response), artworks
