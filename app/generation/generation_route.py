import networkx as nx
import ast
import os
from itertools import combinations
import json
import matplotlib.pyplot as plt
import cv2
import uuid

from embeddings.embeddings_similarity import search
import settings.settings

class MuseumRouteBuilder:
    def __init__(self, graph_file, background_image_path):
        self.background_image_path = background_image_path
        self.graph_file = graph_file
        with open(self.graph_file, "r", encoding="utf-8") as f:
            self.graph_data = json.load(f)
            
    def load_graph(self):
        """Загрузка графа из JSON-файла."""
        G = nx.Graph()
        for node in self.graph_data["nodes"]:
            G.add_node(
                node["id"],
                x=node["x"],
                y=node["y"],
                pos=(node["x"], node["y"])  # Добавляем сразу pos
            )
        for edge in self.graph_data["edges"]:
            G.add_edge(edge["from"], edge["to"], weight=edge["distance"])
        return G

    def select_optimal_nodes(self, G, nodes_list):
        """Выбирает оптимальные узлы для маршрута."""
        selected_nodes = []
        nodes_to_visit = ['0']  # Начальная точка
        node_to_entry_map = {} 

        for entry in nodes_list:
            if isinstance(entry, str) and entry.startswith('[') and entry.endswith(']'):
                # Это строка-список → разбираем и выбираем лучший
                entry_list = [str(x) for x in ast.literal_eval(entry)]
                best_node = self.select_best_node(G, entry_list)
                if best_node is not None:
                    selected_nodes.append(best_node)
                node_to_entry_map[best_node] = entry
            else:
                # Это одиночный узел → просто добавляем
                if G.has_node(entry):
                    selected_nodes.append(entry)
                    node_to_entry_map[entry] = entry
        nodes_to_visit.extend(selected_nodes)
        return nodes_to_visit, node_to_entry_map 

    def select_best_node(self, G, nodes):
        """Для нескольких узлов выбирает оптимальный узел по минимальной длине маршрута."""
        best_node = None
        best_length = float('inf')
        for node in nodes:
            route_length = 0
            for other_node in nodes:
                if node != other_node:
                    try:
                        route_length += nx.shortest_path_length(G, source=node, target=other_node, weight='distance')
                    except nx.NetworkXNoPath:
                        route_length = float('inf')
                        break
        if route_length < best_length:
                best_length = route_length
                best_node = node

        return best_node

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
    
    def draw_colored_route(self, G, full_real_path, improved_route):
        """Визуализирует маршрут и возвращает изображение в BytesIO для Telegram."""
        image = cv2.imread(self.background_image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        pos = nx.get_node_attributes(G, "pos")
        subgraph = nx.Graph()
        for i in range(len(full_real_path) - 1):
            u, v = full_real_path[i], full_real_path[i + 1]
            if G.has_edge(u, v):
                subgraph.add_edge(u, v)
        for node in full_real_path:
            subgraph.add_node(node)

        node_colors = ['#8b00ff' if node in improved_route else '#cccccc' for node in subgraph.nodes]
        node_size = [200 if node in improved_route else 100 for node in subgraph.nodes]

        random_filename = str(uuid.uuid4()) + '.jpg' 
        output_image_path = os.path.join('data', 'images', random_filename)

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(image)
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        nx.draw(subgraph,
                pos,
                ax=ax,
                with_labels=True,
                node_color=node_colors,
                edge_color="orange",
                node_size=node_size,
                font_size=7,
                width=2,
                font_color="white")

        plt.axis('off')
        plt.savefig(output_image_path, dpi=300, bbox_inches='tight', pad_inches=0)
        plt.close()

        return output_image_path

    def build_route(self, G, retrieved_documents, k=5):
        """Основная функция построения маршрута."""
        node_ids = retrieved_documents['nodes']
        # Выбираем узлы для посещения
        nodes_to_visit, node_to_entry_map  = self.select_optimal_nodes(G, node_ids)

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

        full_real_path = self.build_full_route(G, improved_route)

        print("✅ Полный маршрут по всем узлам:", full_real_path)

        output_image_path = self.draw_colored_route(G, full_real_path, improved_route)

        # Собираем информацию о произведениях
        ordered_artworks = []
        added_nodes  = set()
        for node in improved_route:
            if node == '0':
                continue
            if node not in added_nodes:
                original_entry = node_to_entry_map.get(node, node)
                try:
                    index = retrieved_documents['nodes'].index(original_entry)
                except ValueError:
                    print(f"⚠ Не найден индекс для {node} (original_entry={original_entry})")
                    continue
                ordered_artworks.append({
                    "id": node,
                    "name": retrieved_documents['name'][index] if index < len(retrieved_documents['name']) else "",
                    "text": retrieved_documents['text'][index] if index < len(retrieved_documents['text']) else "",
                    "short_description": retrieved_documents['short_description'][index] if index < len(retrieved_documents['short_description']) else "",
                    "image": retrieved_documents['image'][index] if index < len(retrieved_documents['image']) else ""
                })
                added_nodes.add(node)

        return improved_route, ordered_artworks, output_image_path

    
    async def generate_route(self, k, user_description, user_query):
        """Генерация маршрута с помощью GigaChat."""
        scores, retrieved_documents = search(user_query, k)
        print(f"Retrived nodes {retrieved_documents['nodes']}")
        G = self.load_graph()
        route, ordered_artworks, output_image_path = self.build_route(G, retrieved_documents, k)
        lines = []
        for idx, artwork in enumerate(ordered_artworks, start=1):
            name = artwork.get("name", "Без названия")
            artwork_id = artwork.get("id", "нет id")
            line = f"{idx}. {name}\n Экспонат на карте: {artwork_id}"
            lines.append(line)

        text = "\n\n".join(lines)

        return text, ordered_artworks, output_image_path
    
graph_file = settings.settings.GRAPH_FILE
background_image_path = settings.settings.BACKGROUND_IMAGE_PATH

route_builder = MuseumRouteBuilder(graph_file, background_image_path)