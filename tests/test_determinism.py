from algorithms.dijkstra import dijkstra
from algorithms.knapsack import knapsack


def test_dijkstra_equal_cost_routes_pick_same_path_every_time():
    # Two routes S-A-F and S-B-F both cost 2.
    # Rule: the alphabetically earlier node (A) is expanded first.
    nodes = ["S", "A", "B", "F"]
    edges = [
        {"from": "S", "to": "A", "weight": 1, "blocked": False},
        {"from": "S", "to": "B", "weight": 1, "blocked": False},
        {"from": "A", "to": "F", "weight": 1, "blocked": False},
        {"from": "B", "to": "F", "weight": 1, "blocked": False},
    ]
    paths = [dijkstra(nodes, edges, "S", "F")["path"] for _ in range(5)]
    assert all(p == ["S", "A", "F"] for p in paths)


def test_knapsack_equal_score_prefers_earlier_coin():
    # Budget 3: c1 (cost 2) and c2 (cost 3) both give score 3,
    # and only one of them fits, so this is a real tie.
    # Rule: on a tie, the earlier coin in the list is kept.
    coins = [
        {"id": "c1", "cost": 2, "value": 3},
        {"id": "c2", "cost": 3, "value": 3},
    ]
    results = [knapsack(3, coins)["selected"] for _ in range(5)]
    assert all(r == ["c1"] for r in results)