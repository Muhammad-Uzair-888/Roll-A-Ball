# Roll a Ball Algorithm API

Base URL (production): `https://YOUR-API-PROJECT.vercel.app`
Local development: `http://127.0.0.1:8000`

All requests and responses use JSON. Algorithm endpoints use POST.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Check the API is running |
| POST | `/api/dijkstra` | Minimum-cost route through a graph |
| POST | `/api/knapsack` | Best coin selection within an energy budget |

## Health

Response, HTTP 200:

```json
{"status": "ok", "service": "roll-a-ball-algorithms", "version": "1.0"}
```

## Dijkstra: `POST /api/dijkstra`

### Request

```json
{
  "graph": {
    "nodes": ["S", "A", "B", "C", "F"],
    "edges": [
      {"from": "S", "to": "A", "weight": 2},
      {"from": "S", "to": "B", "weight": 5},
      {"from": "A", "to": "C", "weight": 3},
      {"from": "B", "to": "C", "weight": 1},
      {"from": "C", "to": "F", "weight": 2}
    ],
    "blocked_edges": [{"from": "S", "to": "B"}]
  },
  "source": "S",
  "destination": "F",
  "include_trace": true
}
```

Fields:
- `graph.nodes`: string IDs, non-empty, unique. Between 8 and 16 nodes.
- `graph.edges`: roads with integer `weight` ≥ 0. At most 30 edges. Roads are two-way (undirected), so `S→A` and `A→S` are the same road. Each road may appear only once.
- `graph.blocked_edges`: roads to exclude. Each must match a road in `edges`. Direction doesn't matter.
- `source`, `destination`: must be in `nodes`.
- `include_trace`: optional, default `false`.

### Success response, HTTP 200

```json
{
  "success": true,
  "algorithm": "dijkstra",
  "reachable": true,
  "path": ["S", "A", "C", "F"],
  "total_cost": 7,
  "trace": [
    {"step": 1, "event": "initialize", "node": "S", "distance": 0},
    {"step": 2, "event": "visit", "node": "S", "distance": 0},
    {"step": 3, "event": "relax_edge", "from": "S", "to": "A", "new_distance": 2}
  ]
}
```

- `path`: ordered list of node IDs from source to destination.
- `total_cost`: sum of weights along the path.
- `trace`: empty list `[]` unless `include_trace` is `true`.

Trace events, in order:
- `initialize`: starting node and distance 0.
- `visit`: a node is finalized, with its distance.
- `relax_edge`: a shorter distance was found for a neighbor. `from` is the node being expanded, `to` is the neighbor, `new_distance` is the updated distance.

### Unreachable destination, HTTP 200

```json
{"success": true, "algorithm": "dijkstra", "reachable": false, "path": [], "total_cost": null, "trace": []}
```

An unreachable destination is a normal result, not an error.

## Knapsack: `POST /api/knapsack`

### Request

```json
{
  "budget": 10,
  "coins": [
    {"id": "c1", "cost": 5, "value": 10},
    {"id": "c2", "cost": 4, "value": 40}
  ],
  "include_trace": true
}
```

Fields:
- `budget`: integer from 0 to 30.
- `coins`: 1 to 12 coins. Each has a non-empty string `id` (unique), an integer `cost` ≥ 0, and an integer `value` ≥ 0.
- `include_trace`: optional, default `false`.

Each coin can be selected at most once. A coin whose cost exceeds the budget is never selected.

### Success response, HTTP 200

```json
{
  "success": true,
  "algorithm": "knapsack",
  "budget": 10,
  "selected_coin_ids": ["c1", "c2"],
  "total_cost": 9,
  "maximum_score": 50,
  "trace": {
    "dp_table": [
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 10, 10, 10, 10, 10, 10],
      [0, 0, 0, 0, 40, 40, 40, 40, 40, 50, 50]
    ]
  }
}
```

- `selected_coin_ids`: the chosen coins. Order is not guaranteed; compare sorted lists.
- `maximum_score`: total value of the selected coins.
- `total_cost`: total energy used.
- `trace`: empty object `{}` unless `include_trace` is `true`.
- `dp_table`: one row per coin, plus a first row of zeros. Columns are budgets 0 through `budget`. Cell `[i][b]` is the best score using the first `i` coins with budget `b`.

## Errors

Every error uses this envelope:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_GRAPH",
    "message": "A blocked edge does not match any edge in edges.",
    "details": [],
    "request_id": "7f3c2a9e-1b4d-4e8a-9c1e-2f5a6b7c8d9e"
  }
}
```

`details` lists field-level problems for validation errors, and is empty otherwise. `request_id` is unique per error, useful for debugging.

| HTTP | Code | When |
|---|---|---|
| 400 | `INVALID_INPUT` | `nodes` or `coins` is empty |
| 400 | `DUPLICATE_NODE` | Repeated node ID |
| 400 | `DUPLICATE_EDGE` | Same road listed twice (either direction) |
| 400 | `DUPLICATE_COIN` | Repeated coin ID |
| 400 | `INVALID_GRAPH` | Source, destination, edge, or blocked edge references a node not in `nodes`; blocked edge not in `edges` |
| 400 | `LIMIT_EXCEEDED` | Graph outside 8–16 nodes, more than 30 edges, or more than 12 coins |
| 404 | `NOT_FOUND` | Unknown path |
| 405 | `METHOD_NOT_ALLOWED` | Wrong HTTP method, for example GET on `/api/dijkstra` |
| 422 | `VALIDATION_ERROR` | Wrong type or value: integer node IDs, negative weight, fractional weight, budget over 30, missing field, empty coin ID, NaN or Infinity |
| 500 | `INTERNAL_ERROR` | Unexpected server error. Generic message only. |

## Frontend integration notes

- Send requests only when a calculation is needed, not on every frame.
- Check `success` first. On `false`, show `error.message`.
- Treat `reachable: false` as a valid result, not an error.
- Send `include_trace: true` only from the Algorithm Lab.
- Handle network failures and timeouts separately from API errors. A failed request must not stop the game loop.

## Sample level (placeholder)

The graph and coins above come from the SDD and are not the final level. Replace them when the level is designed. The API accepts any values within the limits.