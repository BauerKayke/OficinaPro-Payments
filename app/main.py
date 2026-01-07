"""
Oficina Pro Payment API
Tech Challenge FIAP - Microserviço de Pagamentos

Este serviço processa pagamentos via Mercado Pago para o sistema Oficina Pro.
Implementa observabilidade completa: Traces, Métricas e Logs via OpenTelemetry → New Relic.
"""

from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid

from app.routers import api
from app.logging_config import setup_logging, get_logger
from app.telemetry import setup_telemetry, shutdown_telemetry, get_tracer

# Configurar logging estruturado antes de tudo
setup_logging()

# Logger para este módulo
logger = get_logger(__name__)

# Tracer para spans customizados
tracer = get_tracer(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup: Configurar OpenTelemetry
    setup_telemetry(app)

    logger.info("Payment service starting",
                service="oficinapro-payments",
                environment=os.getenv("ENVIRONMENT", "production"),
                telemetry="enabled")
    yield

    # Shutdown: Flush telemetry
    logger.info("Payment service shutting down")
    shutdown_telemetry()


app = FastAPI(
    title="Oficina Pro Payment API",
    description="API for processing payments via Mercado Pago",
    version="1.0.0",
    lifespan=lifespan
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware para logging de requisições HTTP."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Log da requisição
    logger.info("Request started",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                client_ip=request.client.host if request.client else None)

    try:
        response = await call_next(request)

        # Log da resposta
        duration_ms = (time.time() - start_time) * 1000
        logger.info("Request completed",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2))

        # Adicionar headers de correlação
        response.headers["X-Request-ID"] = request_id
        return response

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception("Request failed",
                        request_id=request_id,
                        method=request.method,
                        path=request.url.path,
                        duration_ms=round(duration_ms, 2),
                        error=str(e))
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "request_id": request_id}
        )


@app.get("/health")
async def health_check():
    """Endpoint de health check para Kubernetes."""
    return {"status": "healthy", "service": "oficinapro-payments"}


app.include_router(api.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
