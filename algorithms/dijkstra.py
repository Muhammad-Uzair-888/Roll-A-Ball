import heapq


def dijkstra(nodes, edges, start, goal):
    # Undirected graph: each road can be used in both directions.
    graph = {node: [] for node in nodes}
    for edge in edges:
        if edge["blocked"]:
            continue
        a, b, w = edge["from"], edge["to"], edge["weight"]
        graph[a].append((b, w))
        graph[b].append((a, w))

    distances = {node: None for node in nodes}
    previous = {node: None for node in nodes}
    distances[start] = 0
    queue = [(0, start)]
    visited = set()
    trace = []

    def add(event, **fields):
        trace.append({"step": len(trace) + 1, "event": event, **fields})

    add("initialize", node=start, distance=0)

    while queue:
        current_cost, current = heapq.heappop(queue)
        if current in visited:
            continue
        visited.add(current)
        add("visit", node=current, distance=current_cost)

        for neighbor, weight in graph[current]:
            new_cost = current_cost + weight
            if distances[neighbor] is None or new_cost < distances[neighbor]:
                distances[neighbor] = new_cost
                previous[neighbor] = current
                heapq.heappush(queue, (new_cost, neighbor))
                add("relax_edge", **{"from": current, "to": neighbor, "new_distance": new_cost})

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