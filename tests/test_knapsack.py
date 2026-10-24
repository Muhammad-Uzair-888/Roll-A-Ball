from algorithms.knapsack import knapsack


def test_known_optimum():
    coins = [
        {"id": "c1", "cost": 5, "value": 10},
        {"id": "c2", "cost": 4, "value": 40},
        {"id": "c3", "cost": 3, "value": 30},
    ]
    result = knapsack(10, coins)
    assert sorted(result["selected"]) == ["c2", "c3"]
    assert result["total_value"] == 70
    assert result["total_cost"] == 7


def test_zero_budget():
    coins = [
        {"id": "c1", "cost": 5, "value": 10},
        {"id": "c2", "cost": 4, "value": 40},
    ]
    result = knapsack(0, coins)
    assert result["selected"] == []
    assert result["total_value"] == 0
    assert result["total_cost"] == 0


def test_item_over_budget_is_skipped():
    coins = [
        {"id": "c1", "cost": 6, "value": 100},
        {"id": "c2", "cost": 2, "value": 3},
    ]
    result = knapsack(5, coins)
    assert result["selected"] == ["c2"]
    assert result["total_value"] == 3