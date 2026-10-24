import heapq

def dijkstra(nodes, edges, start, goal):
    graph = {node: [] for node in nodes}
    for edge in edges:
        if edge["blocked"]:
            continue
        graph[edge["from"]].append((edge["to"], edge["weight"]))

    distances = {node: None for node in nodes}
    previous = {node: None for node in nodes}
    distances[start] = 0
    queue = [(0, start)]
    visited = set()
    trace = []

    while queue:
        current_cost, current = heapq.heappop(queue)
        if current in visited:
            continue
        visited.add(current)

        relaxed = []
        for neighbor, weight in graph[current]:
            new_cost = current_cost + weight
            if distances[neighbor] is None or new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous[neighbor] = current
                heapq.heappush(queue, (new_cost, neighbor))
                relaxed.append([current, neighbor])

        trace.append({
            "step": len(trace) + 1,
            "visit": current,
            "distances": dict(distances),
            "relaxed_edges": relaxed,
        })

    if distances[goal] is None:
        return {"reachable": False, "path": [], "total_cost": None, "trace": trace}

    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()

    return {
        "reachable": True,
        "path": path,
        "total_cost": distances[goal],
        "trace": trace,
    }