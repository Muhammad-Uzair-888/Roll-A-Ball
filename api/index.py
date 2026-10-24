from fastapi import FastAPI

app = FastAPI()


@app.get("/api/health")
def health():
    return {"message": "I am alive"}