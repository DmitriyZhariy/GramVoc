from fastapi import FastAPI
from src.database import get_db

app = FastAPI(title="GramVoc API")

@app.get("/health")
async def health_check():
    return {"status": "ok"}