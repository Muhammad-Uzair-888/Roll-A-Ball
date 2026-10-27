from fastapi.testclient import TestClient

from api.index import app

client = TestClient(app)

FILLER_NODES = [f"N{i}" for i in range(1, 20)]


def pad_nodes(nodes):
    if not nodes or len(nodes) >= 8:
        return nodes
    extra = [n for n in FILLER_NODES if n not in nodes][: 8 - len(nodes)]
    return nodes + extra


def dijkstra_body(nodes, edges, source, destination, blocked_edges=None, include_trace=False, pad=True):
    return {
        "graph": {
            "nodes": pad_nodes(nodes) if pad else nodes,
            "edges": edges,
            "blocked_edges": blocked_edges or [],
        },
        "source": source,
        "destination": destination,
        "include_trace": include_trace,
    }

SDD_NODES = ["S", "A", "B", "C", "F"]
SDD_EDGES = [
    {"from": "S", "to": "A", "weight": 2},
    {"from": "S", "to": "B", "weight": 5},
    {"from": "A", "to": "C", "weight": 3},
    {"from": "B", "to": "C", "weight": 1},
    {"from": "C", "to": "F", "weight": 2},
]


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "roll-a-ball-algorithms",
        "version": "1.0",
    }


def test_dijkstra_sdd_example():
    body = dijkstra_body(
        SDD_NODES, SDD_EDGES, "S", "F",
        blocked_edges=[{"from": "S", "to": "B"}],
        include_trace=True,
    )
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["algorithm"] == "dijkstra"
    assert data["path"] == ["S", "A", "C", "F"]
    assert data["total_cost"] == 7
    assert data["trace"][0]["event"] == "initialize"
    assert any(step["event"] == "relax_edge" for step in data["trace"])


def test_dijkstra_blocked_edge_changes_route():
    body = dijkstra_body(
        SDD_NODES, SDD_EDGES, "S", "F",
        blocked_edges=[{"from": "C", "to": "A"}],
    )
    response = client.post("/api/dijkstra", json=body)
    data = response.json()
    assert data["path"] == ["S", "B", "C", "F"]
    assert data["total_cost"] == 8


def test_dijkstra_trace_off_by_default():
    body = dijkstra_body(["S", "F"], [{"from": "S", "to": "F", "weight": 2}], "S", "F")
    response = client.post("/api/dijkstra", json=body)
    assert response.json()["trace"] == []


def test_dijkstra_start_equals_destination():
    body = dijkstra_body(["S", "F"], [], "S", "S")
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == ["S"]
    assert data["total_cost"] == 0


def test_dijkstra_unreachable_is_200():
    body = dijkstra_body(["S", "F"], [], "S", "F")
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["reachable"] is False
    assert data["path"] == []
    assert data["total_cost"] is None


def test_dijkstra_road_works_in_reverse():
    body = dijkstra_body(["S", "F"], [{"from": "F", "to": "S", "weight": 3}], "S", "F")
    response = client.post("/api/dijkstra", json=body)
    data = response.json()
    assert data["reachable"] is True
    assert data["path"] == ["S", "F"]
    assert data["total_cost"] == 3


def test_dijkstra_edge_node_not_in_nodes_is_400():
    body = dijkstra_body(["S", "F"], [{"from": "S", "to": "Z", "weight": 1}], "S", "F")
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_GRAPH"
    assert data["error"]["request_id"]


def test_dijkstra_blocked_node_not_in_nodes_is_400():
    body = dijkstra_body(
        ["S", "F"], [{"from": "S", "to": "F", "weight": 1}], "S", "F",
        blocked_edges=[{"from": "S", "to": "Z"}],
    )
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_GRAPH"


def test_dijkstra_blocked_edge_not_in_edges_is_400():
    body = dijkstra_body(
        ["S", "A", "F"],
        [{"from": "S", "to": "A", "weight": 1}],
        "S", "F",
        blocked_edges=[{"from": "A", "to": "F"}],
    )
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_GRAPH"


def test_dijkstra_negative_weight_is_422():
    body = dijkstra_body(["S", "F"], [{"from": "S", "to": "F", "weight": -3}], "S", "F")
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_dijkstra_integer_node_ids_are_422():
    body = dijkstra_body([0, 1], [{"from": 0, "to": 1, "weight": 1}], 0, 1)
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_dijkstra_empty_node_id_is_422():
    body = dijkstra_body(["", "F"], [], "F", "F")
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 422


def test_dijkstra_duplicate_node_is_400():
    body = dijkstra_body(["S", "S", "F"], [], "S", "F")
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DUPLICATE_NODE"


def test_dijkstra_empty_nodes_is_400():
    body = dijkstra_body([], [], "S", "S")
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_dijkstra_duplicate_edge_is_400():
    body = dijkstra_body(
        ["S", "F"],
        [{"from": "S", "to": "F", "weight": 1}, {"from": "S", "to": "F", "weight": 5}],
        "S", "F",
    )
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DUPLICATE_EDGE"


def test_dijkstra_reversed_duplicate_edge_is_400():
    body = dijkstra_body(
        ["S", "F"],
        [{"from": "S", "to": "F", "weight": 1}, {"from": "F", "to": "S", "weight": 1}],
        "S", "F",
    )
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DUPLICATE_EDGE"


def test_dijkstra_flat_format_is_422():
    old_body = {
        "nodes": ["S", "F"],
        "edges": [{"from": "S", "to": "F", "weight": 1}],
        "start": "S",
        "goal": "F",
    }
    response = client.post("/api/dijkstra", json=old_body)
    assert response.status_code == 422


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
    assert data["success"] is True
    assert data["algorithm"] == "knapsack"
    assert sorted(data["selected_coin_ids"]) == ["c1", "c2"]
    assert data["maximum_score"] == 50
    assert data["total_cost"] == 9
    assert data["trace"] == {}


def test_knapsack_trace_on_when_requested():
    body = {
        "budget": 10,
        "coins": [{"id": "c1", "cost": 5, "value": 10}],
        "include_trace": True,
    }
    data = client.post("/api/knapsack", json=body).json()
    assert len(data["trace"]["dp_table"]) == 2


def test_knapsack_budget_over_30_is_422():
    body = {"budget": 31, "coins": [{"id": "c1", "cost": 1, "value": 1}]}
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_knapsack_negative_cost_is_422():
    body = {"budget": 5, "coins": [{"id": "c1", "cost": -1, "value": 1}]}
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 422


def test_knapsack_duplicate_coin_is_400():
    body = {
        "budget": 5,
        "coins": [
            {"id": "c1", "cost": 1, "value": 1},
            {"id": "c1", "cost": 2, "value": 2},
        ],
    }
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DUPLICATE_COIN"


def test_knapsack_empty_coins_is_400():
    body = {"budget": 5, "coins": []}
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_knapsack_empty_coin_id_is_422():
    body = {"budget": 5, "coins": [{"id": "", "cost": 1, "value": 1}]}
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 422


def test_unknown_endpoint_returns_envelope():
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_wrong_method_returns_envelope():
    response = client.get("/api/dijkstra")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_validation_error_lists_fields():
    response = client.post("/api/knapsack", json={"budget": 10})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0


def test_unexpected_error_returns_generic_500(monkeypatch):
    import api.index as index

    def broken(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(index, "knapsack", broken)
    safe_client = TestClient(app, raise_server_exceptions=False)
    body = {"budget": 5, "coins": [{"id": "c1", "cost": 1, "value": 1}]}
    response = safe_client.post("/api/knapsack", json=body)
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_ERROR"
    assert "secret" not in response.text

def test_dijkstra_below_min_nodes_is_400():
    body = dijkstra_body(["S", "F"], [], "S", "F", pad=False)
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "LIMIT_EXCEEDED"


def test_dijkstra_above_max_nodes_is_400():
    nodes = [f"N{i}" for i in range(17)]
    body = dijkstra_body(nodes, [], "N0", "N1", pad=False)
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "LIMIT_EXCEEDED"


def test_dijkstra_16_nodes_is_allowed():
    nodes = [f"N{i}" for i in range(16)]
    body = dijkstra_body(nodes, [], "N0", "N1", pad=False)
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 200


def test_dijkstra_30_edges_is_allowed():
    from itertools import combinations

    nodes = [f"N{i}" for i in range(16)]
    roads = list(combinations(range(16), 2))[:30]
    edges = [{"from": f"N{a}", "to": f"N{b}", "weight": 1} for a, b in roads]
    body = dijkstra_body(nodes, edges, "N0", "N1", pad=False)
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 200


def test_dijkstra_31_edges_is_400():
    from itertools import combinations

    nodes = [f"N{i}" for i in range(16)]
    roads = list(combinations(range(16), 2))[:31]
    edges = [{"from": f"N{a}", "to": f"N{b}", "weight": 1} for a, b in roads]
    body = dijkstra_body(nodes, edges, "N0", "N1", pad=False)
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "LIMIT_EXCEEDED"


def test_knapsack_12_coins_is_allowed():
    coins = [{"id": f"c{i}", "cost": 1, "value": 1} for i in range(12)]
    response = client.post("/api/knapsack", json={"budget": 5, "coins": coins})
    assert response.status_code == 200


def test_knapsack_13_coins_is_400():
    coins = [{"id": f"c{i}", "cost": 1, "value": 1} for i in range(13)]
    response = client.post("/api/knapsack", json={"budget": 5, "coins": coins})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "LIMIT_EXCEEDED"

def test_cors_allows_configured_origin():
    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_blocks_unknown_origin():
    response = client.get("/api/health", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in response.headers


def test_dijkstra_nan_weight_is_422():
    raw = (
        '{"graph": {"nodes": ["S", "F"], '
        '"edges": [{"from": "S", "to": "F", "weight": NaN}], "blocked_edges": []}, '
        '"source": "S", "destination": "F", "include_trace": false}'
    )
    response = client.post(
        "/api/dijkstra",
        content=raw,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_dijkstra_infinite_weight_is_422():
    raw = (
        '{"graph": {"nodes": ["S", "F"], '
        '"edges": [{"from": "S", "to": "F", "weight": Infinity}], "blocked_edges": []}, '
        '"source": "S", "destination": "F", "include_trace": false}'
    )
    response = client.post(
        "/api/dijkstra",
        content=raw,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["success"] is False

def test_dijkstra_fractional_weight_is_422():
    body = dijkstra_body(["S", "F"], [{"from": "S", "to": "F", "weight": 1.5}], "S", "F")
    response = client.post("/api/dijkstra", json=body)
    assert response.status_code == 422


def test_knapsack_fractional_cost_is_422():
    body = {"budget": 5, "coins": [{"id": "c1", "cost": 1.5, "value": 1}]}
    response = client.post("/api/knapsack", json=body)
    assert response.status_code == 422