from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from decimal import Decimal

class PaymentMethod(str, Enum):
    PIX = "PIX"
    CREDIT_CARD = "CARTAO_CREDITO"
    DEBIT_CARD = "CARTAO_DEBITO"
    BOLETO = "BOLETO"

class CardData(BaseModel):
    card_number: str = Field(..., min_length=13, max_length=19, description="Card number")
    cardholder_name: str = Field(..., min_length=1, description="Cardholder name")
    expiration_date: str = Field(..., pattern=r"\d{2}/\d{2}", description="MM/YY")
    security_code: str = Field(..., min_length=3, max_length=4, description="CVV/CVC")
    installments: int = Field(default=1, ge=1, description="Number of installments")

class PaymentRequest(BaseModel):
    order_id: int = Field(..., description="Order Service ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    method: PaymentMethod = Field(..., description="Payment method")
    description: str = Field(..., description="Payment description")

    card_data: Optional[CardData] = None
    payer_email: str = Field(..., description="Payer email for notification")
    payer_cpf: Optional[str] = Field(None, description="Payer CPF (required for Boleto/Pix sometimes)")

class PaymentResponse(BaseModel):
    success: bool
    transaction_id: str
    message: str
    status: str
    qr_code: Optional[str] = None
    qr_code_base64: Optional[str] = None
    ticket_url: Optional[str] = None

class PaymentStatusResponse(BaseModel):
    transaction_id: str
    status: str
    status_detail: str


class RefundRequest(BaseModel):
    """Requisição de estorno de pagamento."""
    transaction_id: str = Field(..., description="ID da transação a ser estornada")
    amount: Optional[Decimal] = Field(None, gt=0, description="Valor a estornar (None = estorno total)")
    reason: Optional[str] = Field(None, description="Motivo do estorno")


class RefundResponse(BaseModel):
    """Resposta do estorno de pagamento."""
    success: bool
    refund_id: Optional[str] = None
    transaction_id: str
    message: str
    status: str
    amount_refunded: Optional[Decimal] = None
