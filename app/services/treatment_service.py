# import math
# import heapq
# import random

# def build_graph(connections):
#     graph = {}

#     for c in connections:
#         graph.setdefault(c.hospital_from, []).append({
#             "to": c.hospital_to,
#             "cost": c.transfer_cost,
#             "latency": c.latency_minutes,
#             "reliability": c.reliability
#         })

#     return graph

# def shortest_cost_path(graph, start, end):
#     pq = [(0, start, [])]
#     visited = set()

#     while pq:
#         cost, node, path = heapq.heappop(pq)

#         if node in visited:
#             continue
#         visited.add(node)

#         path = path + [node]

#         if node == end:
#             return cost, path

#         for edge in graph.get(node, []):
#             heapq.heappush(
#                 pq,
#                 (cost + edge["cost"], edge["to"], path)
#             )

#     return None
# def shortest_latency_path(graph, start, end):
#     pq = [(0, start, [])]
#     visited = set()

#     while pq:
#         latency, node, path = heapq.heappop(pq)

#         if node in visited:
#             continue
#         visited.add(node)

#         path = path + [node]

#         if node == end:
#             return latency, path

#         for edge in graph.get(node, []):
#             heapq.heappush(
#                 pq,
#                 (latency + edge["latency"], edge["to"], path)
#             )

#     return None
# def most_reliable_path(graph, start, end):
#     pq = [(0, start, [])]  # negative log
#     visited = set()

#     while pq:
#         neg_log_r, node, path = heapq.heappop(pq)

#         if node in visited:
#             continue
#         visited.add(node)

#         path = path + [node]

#         if node == end:
#             reliability = math.exp(-neg_log_r)
#             return reliability, path

#         for edge in graph.get(node, []):
#             weight = -math.log(edge["reliability"])
#             heapq.heappush(
#                 pq,
#                 (neg_log_r + weight, edge["to"], path)
#             )

#     return None

# def compute_transfer(graph, path):
#     total_cost = 0
#     total_latency = 0
#     reliability = 1

#     for i in range(len(path) - 1):
#         edge = next(
#             e for e in graph[path[i]] if e["to"] == path[i+1]
#         )

#         total_cost += edge["cost"]
#         total_latency += edge["latency"]
#         reliability *= edge["reliability"]

#     success = random.random() <= reliability

#     return {
#         "cost": round(total_cost, 2),
#         "latency": round(total_latency, 2),
#         "reliability": round(reliability, 4),
#         "success": success
#     }

