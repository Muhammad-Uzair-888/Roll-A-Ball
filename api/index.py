from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

from algorithms.dijkstra import dijkstra
from algorithms.knapsack import knapsack

app = FastAPI()


class Edge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: int = Field(alias="from")
    to: int
    weight: int = Field(ge=0)
    blocked: bool = False


class DijkstraRequest(BaseModel):
    nodes: List[int]
    edges: List[Edge]
    start: int
    goal: int


class Coin(BaseModel):
    id: str
    cost: int = Field(ge=0)
    value: int = Field(ge=0)


class KnapsackRequest(BaseModel):
    budget: int = Field(ge=0, le=30)
    coins: List[Coin]


@app.exception_handler(HTTPException)
async def http_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"error": str(exc.errors()[0]["msg"])})


@app.get("/api/health")
def health():
    return {"message": "I am alive"}


@app.post("/api/dijkstra")
def run_dijkstra(req: DijkstraRequest):
    node_set = set(req.nodes)

    if req.start not in node_set or req.goal not in node_set:
        raise HTTPException(status_code=422, detail="start and goal must be in nodes")

    for edge in req.edges:
        if edge.from_node not in node_set or edge.to not in node_set:
            raise HTTPException(status_code=422, detail="edge uses a node not in nodes")

    edges = [edge.model_dump(by_alias=True) for edge in req.edges]
    return dijkstra(req.nodes, edges, req.start, req.goal)


@app.post("/api/knapsack")
def run_knapsack(req: KnapsackRequest):
    coins = [coin.model_dump() for coin in req.coins]
    return knapsack(req.budget, coins)