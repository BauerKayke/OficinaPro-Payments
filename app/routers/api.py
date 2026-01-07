"""
Rotas da API de Pagamentos.

Tech Challenge FIAP - Microserviço de Pagamentos
"""

from fastapi import APIRouter, HTTPException
from app.schemas import PaymentRequest, PaymentResponse, RefundRequest, RefundResponse
from app.services.payment_service import PaymentService
from app.logging_config import get_logger

router = APIRouter()
payment_service = PaymentService()
logger = get_logger(__name__)


@router.post("/payments", response_model=PaymentResponse, tags=["Payments"])
async def create_payment(request: PaymentRequest):
    """
    Processa um novo pagamento usando Mercado Pago.

    Suporta: PIX, Cartão de Crédito/Débito, Boleto
    """
    logger.info("Payment request received",
               order_id=request.order_id,
               method=request.method.value,
               amount=float(request.amount))

    response = payment_service.process_payment(request)

    logger.info("Payment processed",
               order_id=request.order_id,
               transaction_id=response.transaction_id,
               success=response.success,
               status=response.status)

    return response


@router.post("/refunds", response_model=RefundResponse, tags=["Refunds"])
async def create_refund(request: RefundRequest):
    """
    Processa um estorno de pagamento.

    Permite estorno total ou parcial de uma transação previamente aprovada.
    """
    logger.info("Refund request received",
               transaction_id=request.transaction_id,
               amount=float(request.amount) if request.amount else "total",
               reason=request.reason)

    response = payment_service.process_refund(request)

    logger.info("Refund processed",
               transaction_id=request.transaction_id,
               refund_id=response.refund_id,
               success=response.success,
               status=response.status)

    return response


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "payment-api"}
