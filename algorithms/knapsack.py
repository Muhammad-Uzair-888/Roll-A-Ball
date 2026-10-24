def knapsack(budget, coins):
    n = len(coins)
    dp = [[0] * (budget + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        cost = coins[i - 1]["cost"]
        value = coins[i - 1]["value"]
        for b in range(budget + 1):
            dp[i][b] = dp[i - 1][b]
            if cost <= b:
                dp[i][b] = max(dp[i][b], dp[i - 1][b - cost] + value)

    selected = []
    trace = []
    b = budget
    for i in range(n, 0, -1):
        included = dp[i][b] != dp[i - 1][b]
        trace.append({
            "coin": coins[i - 1]["id"],
            "budget": b,
            "decision": "included" if included else "excluded",
        })
        if included:
            selected.append(coins[i - 1]["id"])
            b -= coins[i - 1]["cost"]
    selected.reverse()
    trace.reverse()

    chosen = set(selected)
    total_cost = sum(c["cost"] for c in coins if c["id"] in chosen)

    return {
        "selected": selected,
        "total_value": dp[n][budget],
        "total_cost": total_cost,
        "dp_table": dp,
        "trace": trace,
    }