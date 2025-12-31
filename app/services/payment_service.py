import mercadopago
import os
from app.schemas import PaymentRequest, PaymentResponse, PaymentMethod
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        access_token = os.getenv("MP_ACCESS_TOKEN")
        if not access_token:
            logger.warning("MP_ACCESS_TOKEN não encontrado. Integração com Mercado Pago falhará.")
            self.sdk = None
        else:
            self.sdk = mercadopago.SDK(access_token)

    def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        if not self.sdk:
            return self._mock_response(request, success=False, message="Serviço de Pagamento não encontrado")

        try:
            if request.method == PaymentMethod.PIX:
                return self._process_pix(request)
            elif request.method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
                return self._process_card(request)
            elif request.method == PaymentMethod.BOLETO:
                return self._process_boleto(request)
            else:
                return self._mock_response(request, success=False, message="Método de pagamento não implementado")
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            return self._mock_response(request, success=False, message=str(e))

    def _process_pix(self, request: PaymentRequest) -> PaymentResponse:
        payment_data = {
            "transaction_amount": float(request.amount),
            "description": request.description,
            "payment_method_id": "pix",
            "payer": {
                "email": request.payer_email,
                "first_name": "Test",
                "last_name": "User",
                "identification": {
                    "type": "CPF",
                    "number": request.payer_cpf or "19119119100"
                }
            }
        }
        
        return self._create_preference(payment_data, request)

    def _process_card(self, request: PaymentRequest) -> PaymentResponse:
        if not request.card_data:
            return self._mock_response(request, success=False, message="Dados do cartão de crédito ausentes")

        
        
        payment_data = {
            "transaction_amount": float(request.amount),
            "description": request.description,
            "installments": request.card_data.installments,
            "payer": {
                "email": request.payer_email
            }
        }
        
        logger.info("Simulating Card Payment (Real card processing requires frontend tokenization)")
        return self._mock_response(request, success=True, message="Pagamento com cartão de crédito processado (Simulado)")

    def _process_boleto(self, request: PaymentRequest) -> PaymentResponse:
        payment_data = {
            "transaction_amount": float(request.amount),
            "description": request.description,
            "payment_method_id": "bolbradesco", 
            "payer": {
                "email": request.payer_email,
                "first_name": "Test",
                "last_name": "User",
                "identification": {
                    "type": "CPF",
                    "number": request.payer_cpf or "19119119100"
                },
                "address": {
                    "zip_code": "06233-200",
                    "street_name": "Av. das Nações Unidas",
                    "street_number": "3003",
                    "neighborhood": "Bonfim",
                    "city": "Osasco",
                    "federal_unit": "SP"
                }
            }
        }
        return self._create_preference(payment_data, request)

    def _create_preference(self, payment_data, request) -> PaymentResponse:
        logger.info(f"Creating payment with data: {payment_data}")
        payment_response = self.sdk.payment().create(payment_data)
        response = payment_response["response"]
        
        if payment_response["status"] == 201:
            qr_code = response.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code")
            qr_code_base64 = response.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64")
            ticket_url = response.get("transaction_details", {}).get("external_resource_url")
            
            return PaymentResponse(
                success=True,
                transaction_id=str(response.get("id")),
                message="Payment Created",
                status=response.get("status"),
                qr_code=qr_code,
                qr_code_base64=qr_code_base64,
                ticket_url=ticket_url
            )
        else:
             return PaymentResponse(
                success=False,
                transaction_id="",
                message=response.get("message", "Erro desconhecido"),
                status="error"
            )

    def _mock_response(self, request: PaymentRequest, success: bool, message: str) -> PaymentResponse:
        return PaymentResponse(
            success=success,
            transaction_id=f"MOCK-{request.order_id}",
            message=message,
            status="approved" if success else "rejected"
        )
