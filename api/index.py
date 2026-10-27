import os

from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid
from typing import Annotated, List

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

from algorithms.dijkstra import dijkstra
from algorithms.knapsack import knapsack

logger = logging.getLogger("roll_a_ball_api")

NodeId = Annotated[str, Field(min_length=1)]
# Size limits from SDD Section 4 and 6.
MIN_NODES = 8
MAX_NODES = 16
MAX_EDGES = 30
MAX_COINS = 12

app = FastAPI()

# Origins allowed to call the API from a browser. Set ALLOWED_ORIGINS in
# Vercel as a comma-separated list, for example:
# https://roll-a-ball-frontend.vercel.app,http://localhost:5173
_allowed = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _allowed.split(",") if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details=None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def error_response(status_code, code, message, details=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "request_id": str(uuid.uuid4()),
            },
        },
    )


@app.exception_handler(ApiError)
async def api_error_handler(request, exc: ApiError):
    return error_response(exc.status_code, exc.code, exc.message, exc.details)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(part) for part in err["loc"]), "issue": err["msg"]}
        for err in exc.errors()
    ]
    return error_response(422, "VALIDATION_ERROR", "Request body failed validation.", details)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return error_response(404, "NOT_FOUND", "The requested endpoint does not exist.")
    if exc.status_code == 405:
        return error_response(405, "METHOD_NOT_ALLOWED", "This HTTP method is not supported for this endpoint.")
    return error_response(exc.status_code, "HTTP_ERROR", "The request could not be processed.")


@app.exception_handler(Exception)
async def unhandled_error_handler(request, exc: Exception):
    logger.exception("Unhandled server error")
    return error_response(500, "INTERNAL_ERROR", "An unexpected server error occurred.")


class Edge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: NodeId = Field(alias="from")
    to: NodeId
    weight: int = Field(ge=0)


class BlockedEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: NodeId = Field(alias="from")
    to: NodeId


class Graph(BaseModel):
    nodes: List[NodeId]
    edges: List[Edge]
    blocked_edges: List[BlockedEdge] = Field(default_factory=list)


class DijkstraRequest(BaseModel):
    graph: Graph
    source: NodeId
    destination: NodeId
    include_trace: bool = False


class Coin(BaseModel):
    id: str = Field(min_length=1)
    cost: int = Field(ge=0)
    value: int = Field(ge=0)


class KnapsackRequest(BaseModel):
    budget: int = Field(ge=0, le=30)
    coins: List[Coin]
    include_trace: bool = False


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "roll-a-ball-algorithms", "version": "1.0"}


@app.post("/api/dijkstra")
def run_dijkstra(req: DijkstraRequest):
    g = req.graph

    if not g.nodes:
        raise ApiError(400, "INVALID_INPUT", "nodes must not be empty.")

    if not MIN_NODES <= len(g.nodes) <= MAX_NODES:
        raise ApiError(
            400, "LIMIT_EXCEEDED",
            f"graph must have between {MIN_NODES} and {MAX_NODES} nodes.",
        )

    if len(g.edges) > MAX_EDGES:
        raise ApiError(400, "LIMIT_EXCEEDED", f"graph may have at most {MAX_EDGES} edges.")

    if len(set(g.nodes)) != len(g.nodes):
        raise ApiError(400, "DUPLICATE_NODE", "nodes contains a duplicate identifier.")

    node_set = set(g.nodes)

    if req.source not in node_set or req.destination not in node_set:
        raise ApiError(400, "INVALID_GRAPH", "source and destination must be in nodes.")

    roads = set()
    for edge in g.edges:
        if edge.from_node not in node_set or edge.to not in node_set:
            raise ApiError(400, "INVALID_GRAPH", "An edge references a node that is not in nodes.")
        road = frozenset((edge.from_node, edge.to))
        if road in roads:
            raise ApiError(400, "DUPLICATE_EDGE", "The same connection appears more than once.")
        roads.add(road)

    blocked = set()
    for b in g.blocked_edges:
        if b.from_node not in node_set or b.to not in node_set:
            raise ApiError(400, "INVALID_GRAPH", "A blocked edge references a node that is not in nodes.")
        road = frozenset((b.from_node, b.to))
        if road not in roads:
            raise ApiError(400, "INVALID_GRAPH", "A blocked edge does not match any edge in edges.")
        blocked.add(road)

    internal_edges = [
        {
            "from": e.from_node,
            "to": e.to,
            "weight": e.weight,
            "blocked": frozenset((e.from_node, e.to)) in blocked,
        }
        for e in g.edges
    ]

    result = dijkstra(g.nodes, internal_edges, req.source, req.destination)

    return {
        "success": True,
        "algorithm": "dijkstra",
        "reachable": result["reachable"],
        "path": result["path"],
        "total_cost": result["total_cost"],
        "trace": result["trace"] if req.include_trace else [],
    }


@app.post("/api/knapsack")
def run_knapsack(req: KnapsackRequest):
    if not req.coins:
        raise ApiError(400, "INVALID_INPUT", "coins must not be empty.")

    if len(req.coins) > MAX_COINS:
        raise ApiError(400, "LIMIT_EXCEEDED", f"at most {MAX_COINS} coins are allowed.")

    ids = [coin.id for coin in req.coins]
    if len(set(ids)) != len(ids):
        raise ApiError(400, "DUPLICATE_COIN", "coins contains a duplicate identifier.")

    coins = [coin.model_dump() for coin in req.coins]
    result = knapsack(req.budget, coins)

    return {
        "success": True,
        "algorithm": "knapsack",
        "budget": req.budget,
        "selected_coin_ids": result["selected"],
        "total_cost": result["total_cost"],
        "maximum_score": result["total_value"],
        "trace": {"dp_table": result["dp_table"]} if req.include_trace else {},
    }