from fastapi.testclient import TestClient

from api.index import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"message": "I am alive"}


def test_dijkstra_sample_route():
    body = {
        "nodes": [0, 1, 2, 3, 4],
        "edges": [
            {"from": 0, "to": 1, "weight": 4},
            {"from": 0, "to": 2, "weight": 1},
            {"from": 2, "to": 4, "weight": 4},
        ],
        "start": 0,
        "goal": 4,
    }
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == [0, 2, 4]
    assert data["total_cost"] == 5
    assert "relaxed_edges" in data["trace"][0]


def test_dijkstra_start_equals_goal():
    body = {"nodes": [0, 1], "edges": [], "start": 0, "goal": 0}
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == [0]
    assert data["total_cost"] == 0


def test_dijkstra_unreachable_goal_is_200():
    body = {"nodes": [0, 1], "edges": [], "start": 0, "goal": 1}
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 200
    assert response.json()["reachable"] is False


def test_dijkstra_node_not_in_nodes_is_422():
    body = {
        "nodes": [0, 1],
        "edges": [{"from": 0, "to": 9, "weight": 1}],
        "start": 0,
        "goal": 1,
    }
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 422
    assert "error" in response.json()


def test_dijkstra_negative_weight_is_422():
    body = {
        "nodes": [0, 1],
        "edges": [{"from": 0, "to": 1, "weight": -3}],
        "start": 0,
        "goal": 1,
    }
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 422
    assert "error" in response.json()


def test_knapsack_sample_both_coins():
    body = {
        "budget": 10,
        "coins": [
            {"id": "c1", "cost": 5, "value": 10},
            {"id": "c2", "cost": 4, "value": 40},
        ],
    }
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 200
    data = response.json()
    assert sorted(data["selected"]) == ["c1", "c2"]
    assert data["total_value"] == 50
    assert data["total_cost"] == 9


def test_knapsack_budget_over_30_is_422():
    body = {"budget": 31, "coins": [{"id": "c1", "cost": 1, "value": 1}]}
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 422
    assert "error" in response.json()


def test_knapsack_negative_cost_is_422():
    body = {"budget": 5, "coins": [{"id": "c1", "cost": -1, "value": 1}]}
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 422