import networkx as nx
import os
from itertools import combinations
from langchain_gigachat.chat_models import GigaChat
from langchain_core.prompts import ChatPromptTemplate
import json
from dotenv import load_dotenv

from embeddings.embeddings_similarity import search
from process_data.load_data import clean_text

load_dotenv()

class MuseumRouteBuilder:
    def __init__(self, gigachat_token, graph_file="data/Slovcova/graph_with_titles.json"):
        self.giga = GigaChat(credentials=gigachat_token,
                             model='GigaChat',
                             scope="GIGACHAT_API_CORP",
                             verify_ssl_certs=False)
        self.graph_file = graph_file
        self.SYS_PROMPT = """
        You are a museum guide who creates personalized tours for visitors of art exhibitions based on their interests and preferences.

        You have the user description and the user query based on which you create the tour for the user.
        You have a selection of k artworks included in the tour.

        Instructions:
            - Respond in Russian language.
            - Use a communication style that matches the user description (e.g., "you" or "formal you").
            - If the user description is for a child, add a sense of fantasy and avoid complex terms. If the user description is about an art expert, speak to them as a connoisseur. Adapt to other user categories as well.
            - The response must be presented as a clearly formatted numbered list (1., 2., 3., etc.).
            - Each artwork description must start on a new line with a line break separating artworks.
            - Each artwork should be presented in a way that connects with the user's interests.
            - Avoid dry facts – write like a lively guide telling an interesting story.
            - Make sure that the text is clean and structured as a list.

        !!! IMPORTANT !!!
            - Each artwork must begin with a number (1., 2., 3.)
            - Each artwork must be separated by a new line
            - AVOID merging multiple artworks into one paragraph


        Example of a created response 1:

            Если вы хотите насладиться красотой природы и пейзажей, я подготовил для вас такой маршрут:

            1. Пейзаж с руинами, Семен Щедрин. Это уникальная архитектурная фантазия художника, выполненная в стиле пейзажа. На картине изображены различные формы архитектуры древнего Рима, включая огромную арку разрушенного акведука, фонтан со скульптурами женщин и садовника, вид на обелиск, храм и многоколонный храм.
            

            2. Вид в горах Каррары, Николай Ге. Эта картина показывает горы Каррары, где художник жил и рисовал. На ней изображены живописные виды гор и руин, создающие атмосферу романтики и роскоши каштановых лесов.
            

            3. Дубы и платаны. Фраскати, Николай Ге. Этот пейзаж изображает знаменитые дубы и платаны в городе Фраскати, который славится своими песчаными пляжами и культурным контекстом, связанным с европейским литературным романтизмом.
            

            4. Палех. Этюды для картины "Моя родина", Павел Коровин. Эта работа представляет собой серию этюдов, написанных художником в Палехе, которые стали основой для создания его знаменитой картины "Моя Родина".

        Example of a created response for a kid:

            Привет! Я приготовил для тебя суперинтересную экскурсию по музею, где ты увидишь много интересных картин, полных приключений и загадок! Давай посмотрим, что мы сегодня увидим:

            1. Пейзаж с руинами, Семен Щедрин. Это картина, на которой изображены разрушенные здания и старинные арки. Как будто ты путешествуешь в древние времена и исследуешь тайны старинных руин! Ты сможешь увидеть величественные обелиски и таинственные фонтаны, как в настоящих сказках.
            

            2. Вид в горах Каррары, Николай Ге. На этой картине ты увидишь огромные горы, покрытые облаками, как в самых красивых фантастических фильмах! Здесь показаны таинственные руины, и кажется, что они скрывают за собой невероятные приключения. Почувствуй, как будто ты путешествуешь в сказочные земли!
            

            3. Дубы и платаны. Фраскати, Николай Ге. Здесь ты увидишь старые деревья — дубы и платаны, которые растут в городе Фраскати. Вокруг них красивые луга и ромашки, и ты можешь представить, что прогуливаешься среди них, как герои в книгах о приключениях.
            

            4. Палех. Этюды для картины "Моя родина", Павел Коровин. На этой картине ты увидишь маленькие рисунки, которые художник рисовал, чтобы потом создать настоящую картину. Это как если бы ты рисовал свой собственный мир — и каждый рисунок полон истории и чувств.

        """
        self.prompt_template = ChatPromptTemplate([
            ("system", "{sys_prompt}"),
            ("user", "Here are the artworks that should be included in the tour:\n{formatted_artworks}")
        ])

    def load_graph(self):
        """Загрузка графа из JSON-файла."""
        with open(self.graph_file, "r") as f:
            graph_data = json.load(f)

        G = nx.Graph()
        for node in graph_data["nodes"]:
            G.add_node(node["id"], title=node["title"], x=node["x"], y=node["y"])
        for edge in graph_data["edges"]:
            G.add_edge(edge["from"], edge["to"], weight=edge["distance"])

        return G

    def find_artwork_nodes(self, G, titles):
        """Находит узлы, соответствующие данным названиям произведений искусства."""
        artwork_nodes = {}
        for node, data in G.nodes(data=True):
            if data['title'] in titles:
                artwork_nodes.setdefault(data['title'], []).append(node)
        return artwork_nodes

    def select_optimal_nodes(self, G, artwork_nodes):
        """Выбирает оптимальные узлы для маршрута."""
        selected_nodes = []
        nodes_to_visit = ['0']  # Начальная точка

        for title, nodes in artwork_nodes.items():
            if len(nodes) == 1:
                selected_nodes.extend(nodes)  # Если одна точка, добавляем её
            else:
                best_node = self.select_best_node(G, nodes, artwork_nodes)
                selected_nodes.append(best_node)  # Добавляем лучший узел
        nodes_to_visit.extend(selected_nodes)
        return nodes_to_visit

    def select_best_node(self, G, nodes, artwork_nodes):
        """Для нескольких узлов выбирает оптимальный узел по минимальной длине маршрута."""
        best_node = None
        best_length = float('inf')
        other_nodes = [n for t, nodelist in artwork_nodes.items() if t != nodes[0] for n in nodelist]

        for node in nodes:
            route_length = self.calculate_route_length(G, node, other_nodes)
            if route_length < best_length:
                best_length = route_length
                best_node = node

        return best_node

    def calculate_route_length(self, G, node, other_nodes):
        """Вычисляет общую длину маршрута для одного узла по всем остальным узлам."""
        route_length = 0
        for other_node in other_nodes:
            if node != other_node:
                try:
                    route_length += nx.shortest_path_length(G, source=node, target=other_node, weight='distance')
                except nx.NetworkXNoPath:
                    route_length = float('inf')
                    break
        return route_length

    def build_shortest_paths(self, G, nodes_to_visit):
        """Строит матрицу кратчайших путей между узлами маршрута."""
        shortest_paths = {}
        unreachable_pairs = []

        for u, v in combinations(nodes_to_visit, 2):
            try:
                dist = nx.shortest_path_length(G, source=u, target=v, weight='distance')
                shortest_paths[(u, v)] = dist
                shortest_paths[(v, u)] = dist
            except nx.NetworkXNoPath:
                unreachable_pairs.append((u, v))

        return shortest_paths, unreachable_pairs

    def build_reduced_graph(self, shortest_paths, nodes_to_visit):
        """Строит вспомогательный граф с учетом кратчайших путей."""
        G_reduced = nx.Graph()
        for node in nodes_to_visit:
            G_reduced.add_node(node)
        for (u, v), dist in shortest_paths.items():
            G_reduced.add_edge(u, v, distance=dist)
        return G_reduced

    def get_optimal_route(self, G_reduced):
        """Использует алгоритм для поиска оптимального маршрута (TSP)."""
        return nx.approximation.traveling_salesman_problem(G_reduced, weight='distance', cycle=True)

    def build_full_route(self, G, tsp_route):
        """Восстанавливает полный маршрут на основе оптимизированного пути."""
        full_real_path = []
        for i in range(len(tsp_route) - 1):
            try:
                segment = nx.shortest_path(G, source=tsp_route[i], target=tsp_route[i + 1], weight='distance')
                if i > 0:
                    segment = segment[1:]  # чтобы не дублировать узлы
                full_real_path.extend(segment)
            except nx.NetworkXNoPath:
                print(f"⚠ Нет пути между {tsp_route[i]} и {tsp_route[i + 1]}")
        return full_real_path

    def build_route(self, G, retrieved_documents, k=5):
        titles = retrieved_documents['title']
        print(f'titles: {titles}')

        # Находим подходящие узлы по названиям
        artwork_nodes = self.find_artwork_nodes(G, titles)
        print(f'artwork_nodes: {artwork_nodes}')

        # Выбираем узлы для посещения
        nodes_to_visit = self.select_optimal_nodes(G, artwork_nodes)

        # Строим матрицу кратчайших путей
        shortest_paths, unreachable_pairs = self.build_shortest_paths(G, nodes_to_visit)
        if unreachable_pairs:
            print(f"⚠ Не все пары связаны: {unreachable_pairs}")

        # Строим вспомогательный граф
        G_reduced = self.build_reduced_graph(shortest_paths, nodes_to_visit)

        # Строим оптимальный маршрут
        tsp_route = self.get_optimal_route(G_reduced)
        print(f"✅ Краткий маршрут по точкам (до улучшения): {tsp_route}")

        # Улучшаем маршрут (например, используя симулированное отжигание или другие методы)
        improved_route = nx.approximation.simulated_annealing_tsp(
            G_reduced, weight='distance', seed=42, init_cycle=tsp_route
        )

        print(f"✅ Оптимизированный маршрут: {improved_route}")

        # Собираем информацию о произведениях
        ordered_artworks = []
        added_titles = set()
        for node in improved_route:
            if node == '0':
                continue
            title = G.nodes[node].get('title')
            if title in titles and title not in added_titles:
                index = titles.index(title)
                ordered_artworks.append({
                    "title": title,
                    "text": retrieved_documents['text'][index] if index < len(retrieved_documents['text']) else "",
                    "short_description": retrieved_documents['short_description'][index] if index < len(retrieved_documents['short_description']) else "",
                    "image": retrieved_documents['image'][index] if index < len(retrieved_documents['image']) else ""
                })
                added_titles.add(title)

        return improved_route, ordered_artworks

    def format_prompt(self, ordered_artworks, k, user_query=None, description_field='text'):
        """Форматирование запроса для модели."""
        user_content = f"Экспонаты для маршрута:\n"
        
        if user_query:
            user_content += f"User query: {user_query}\n"
        print(k, type(k))
        for i in range(k):
            user_content += f"{i + 1}. {ordered_artworks[i][description_field]}\n"

        return user_content   

    
    def generate_route(self, k, user_description, user_query):
        """Генерация маршрута с помощью GigaChat."""
        scores, retrieved_documents = search(user_query, k)
        G = self.load_graph()
        route, ordered_artworks = self.build_route(G, retrieved_documents, k)
        formatted_artworks = self.format_prompt(ordered_artworks, k, user_query)

        chain = self.prompt_template | self.giga
        response = chain.invoke({
            "sys_prompt": self.SYS_PROMPT,
            "formatted_artworks": formatted_artworks,
            "user_description": user_description
        })

        if len(response.content) < 350:
            print("The BLACKLIST problem. Regeneration with the formatted descriptions.")
            formatted_prompt = self.format_prompt(ordered_artworks, k, user_query, description_field='short_description')

            response = chain.invoke({
                "sys_prompt": self.SYS_PROMPT,
                "formatted_artworks": formatted_prompt,
                "user_description": user_description
            })

        if len(response.content) < 350:
            print("The BLACKLIST problem. Sending the list of formatted descriptions.")
            user_content = f"Список экспонатов:\n"
            for i in range(k):
                user_content += f"{i + 1}. {clean_text(ordered_artworks[i]['short_description'])}\n\n"
            response = user_content

        description_field = 'short_description' if len(response.content) < 350 else 'text'

        artworks = [
            {
                "text": ordered_artwork.get(description_field, ''),
                "image": ordered_artwork.get('image', '')
            }
            for ordered_artwork in ordered_artworks[:k]
        ]

        return response.content if hasattr(response, 'content') else str(response), artworks
    
gigachat_token = os.getenv("GIGACHAT_TOKEN")
graph_file = os.getenv('GRAPH_FILE')

route_builder = MuseumRouteBuilder(gigachat_token, graph_file)
