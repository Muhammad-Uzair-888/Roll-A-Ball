from algorithms.dijkstra import dijkstra


def test_picks_cheaper_route():
    nodes = [0, 1, 2, 3, 4]
    edges = [
        {"from": 0, "to": 1, "weight": 4, "blocked": False},
        {"from": 0, "to": 2, "weight": 1, "blocked": False},
        {"from": 2, "to": 4, "weight": 4, "blocked": False},
        {"from": 1, "to": 4, "weight": 1, "blocked": False},
    ]
    result = dijkstra(nodes, edges, 0, 4)
    assert result["reachable"] is True
    assert result["path"] == [0, 2, 4]
    assert result["total_cost"] == 5


def test_equal_cost_routes():
    nodes = [0, 1, 2, 3]
    edges = [
        {"from": 0, "to": 1, "weight": 1, "blocked": False},
        {"from": 0, "to": 2, "weight": 1, "blocked": False},
        {"from": 1, "to": 3, "weight": 1, "blocked": False},
        {"from": 2, "to": 3, "weight": 1, "blocked": False},
    ]
    result = dijkstra(nodes, edges, 0, 3)
    assert result["reachable"] is True
    assert result["total_cost"] == 2
    assert result["path"] in ([0, 1, 3], [0, 2, 3])


def test_blocked_edge_is_skipped():
    nodes = [0, 1, 2]
    edges = [
        {"from": 0, "to": 1, "weight": 1, "blocked": True},
        {"from": 0, "to": 2, "weight": 1, "blocked": False},
        {"from": 2, "to": 1, "weight": 1, "blocked": False},
    ]
    result = dijkstra(nodes, edges, 0, 1)
    assert result["path"] == [0, 2, 1]
    assert result["total_cost"] == 2


def test_unreachable_goal():
    nodes = [0, 1]
    edges = []
    result = dijkstra(nodes, edges, 0, 1)
    assert result["reachable"] is False
    assert result["path"] == []
    assert result["total_cost"] is None