from fastapi import APIRouter, HTTPException, Depends
from app.schemas import PaymentRequest, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter()
payment_service = PaymentService()

@router.post("/payments", response_model=PaymentResponse, tags=["Payments"])
async def create_payment(request: PaymentRequest):
    """
    Processa um novo pagamento usando Mercado Pago.
    """
    return payment_service.process_payment(request)

@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
