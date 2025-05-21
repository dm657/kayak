from typing import Callable

import networkx as nx


# def build_graph(preference_lists):
#     G = nx.DiGraph()
#     edge_weights = defaultdict(int)
#
#     # Добавляем рёбра с учётом предпочтений
#     for lst in preference_lists:
#         for i in range(len(lst) - 1):
#             for j in range(i + 1, len(lst)):
#                 edge_weights[(lst[i], lst[j])] += 1  # lst[i] предпочтительнее lst[j]
#
#     # Добавляем рёбра в граф
#     for (a, b), weight in edge_weights.items():
#         G.add_edge(a, b, weight=weight)
#     # print(f'{edge_weights=}')
#     return G


def graph_builder(user_id: int = None) -> Callable:
    if user_id:
        def build_graph(edges_lists: list[list[int]]):
            G = nx.DiGraph()
            for a, b in edges_lists:
                G.add_edge(b, a, weight=1)
            return G
        return build_graph

    else:
        def build_graph(edges_lists: list[list[int]]):
            G = nx.DiGraph()
            for a, b, weight in edges_lists:
                G.add_edge(b, a, weight=weight)
            #
            # print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')
            # for u, v, data in G.edges(data=True):
            #     print(f"{u} -> {v}, weight = {data['weight']}")

            return G
        return build_graph


def compute_pagerank(g) -> dict:
    data = nx.pagerank(g, weight='weight')
    return data
