from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI
from app.routers import api

app = FastAPI(
    title="Oficina Pro Payment API",
    description="API for processing payments via Mercado Pago",
    version="1.0.0"
)

app.include_router(api.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
