"""
Serviço de processamento de pagamentos via Mercado Pago.

Tech Challenge FIAP - Microserviço de Pagamentos
Implementa integração com Mercado Pago para PIX, Cartão e Boleto.
Inclui traces OpenTelemetry para observabilidade.
"""

import mercadopago
import os
from app.schemas import PaymentRequest, PaymentResponse, PaymentMethod, RefundRequest, RefundResponse
from app.logging_config import get_logger
from app.telemetry import get_tracer, get_meter, force_flush_metrics
from app.database.dynamodb import DynamoDBPaymentRepository
from opentelemetry import trace

# Logger estruturado para observabilidade
logger = get_logger(__name__)

# Tracer e Meter para OpenTelemetry
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# Métricas customizadas
payment_counter = meter.create_counter(
    name="payment.processed.total",
    description="Total de pagamentos processados",
    unit="1"
)

payment_duration = meter.create_histogram(
    name="payment.duration.ms",
    description="Duração do processamento de pagamento",
    unit="ms"
)

refund_counter = meter.create_counter(
    name="refund.processed.total",
    description="Total de estornos processados",
    unit="1"
)

class PaymentService:
    def __init__(self):
        access_token = os.getenv("MP_ACCESS_TOKEN")
        if not access_token:
            logger.warning("Mercado Pago access token not found",
                          error="MP_ACCESS_TOKEN environment variable not set")
            self.sdk = None
        else:
            logger.info("Payment service initialized", provider="mercadopago")
            self.sdk = mercadopago.SDK(access_token)
        
        # Inicializar repositório DynamoDB (NoSQL - Requisito Fase 4)
        try:
            self.payment_repository = DynamoDBPaymentRepository()
            logger.info("DynamoDB repository initialized", 
                       database="dynamodb",
                       requirement="Fase 4 NoSQL")
        except Exception as e:
            logger.error("Failed to initialize DynamoDB repository", error=str(e))
            self.payment_repository = None

    def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Processa um pagamento com tracing OpenTelemetry."""
        import time
        start_time = time.time()

        # Criar span para rastrear a operação de pagamento
        with tracer.start_as_current_span("payment.process") as span:
            # Adicionar atributos ao span
            span.set_attribute("payment.order_id", request.order_id)
            span.set_attribute("payment.method", request.method.value)
            span.set_attribute("payment.amount", float(request.amount))
            span.set_attribute("payment.payer_email", request.payer_email)

            if not self.sdk:
                span.set_attribute("payment.success", False)
                span.set_attribute("payment.error", "SDK not configured")
                return self._mock_response(request, success=False, message="Serviço de Pagamento não encontrado")

            try:
                if request.method == PaymentMethod.PIX:
                    response = self._process_pix(request)
                elif request.method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
                    response = self._process_card(request)
                elif request.method == PaymentMethod.BOLETO:
                    response = self._process_boleto(request)
                else:
                    response = self._mock_response(request, success=False, message="Método de pagamento não implementado")

                # Registrar resultado no span
                span.set_attribute("payment.success", response.success)
                span.set_attribute("payment.status", response.status)
                span.set_attribute("payment.transaction_id", response.transaction_id)

                # Registrar métricas
                duration_ms = (time.time() - start_time) * 1000
                payment_counter.add(1, {
                    "method": request.method.value,
                    "success": str(response.success),
                    "status": response.status
                })
                payment_duration.record(duration_ms, {
                    "method": request.method.value,
                    "success": str(response.success)
                })

                # Flush síncrono de métricas para envio imediato
                force_flush_metrics(timeout_millis=500)

                # Persistir pagamento no DynamoDB (NoSQL - Requisito Fase 4)
                if self.payment_repository:
                    try:
                        payment_data = {
                            'order_id': request.order_id,
                            'amount': float(request.amount),
                            'method': request.method.value,
                            'status': response.status,
                            'transaction_id': response.transaction_id,
                            'payer_email': request.payer_email,
                            'description': request.description,
                            'success': response.success,
                            'message': response.message,
                            'payment_url': response.payment_url or '',
                            'qr_code': response.qr_code or '',
                            'qr_code_base64': response.qr_code_base64 or '',
                            'barcode_content': response.barcode_content or ''
                        }
                        saved = self.payment_repository.create_payment(payment_data)
                        span.set_attribute("dynamodb.saved", True)
                        span.set_attribute("dynamodb.payment_id", saved['payment_id'])
                        logger.info("Payment persisted in DynamoDB",
                                   payment_id=saved['payment_id'],
                                   order_id=request.order_id,
                                   database="dynamodb")
                    except Exception as db_error:
                        logger.error("Failed to persist payment in DynamoDB",
                                   error=str(db_error),
                                   order_id=request.order_id)
                        # Não falhar a operação se DynamoDB falhar
                        span.set_attribute("dynamodb.error", str(db_error))

                return response

            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                logger.exception("Payment processing failed",
                               order_id=request.order_id,
                               method=request.method.value,
                               amount=float(request.amount),
                               error=str(e))
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

        logger.info("Card payment simulated",
                   order_id=request.order_id,
                   method="card",
                   amount=float(request.amount),
                   note="Real card processing requires frontend tokenization")
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
        logger.info("Creating payment preference",
                   order_id=request.order_id,
                   method=request.method.value,
                   amount=payment_data.get("transaction_amount"),
                   payer_email=payment_data.get("payer", {}).get("email"))
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

    def process_refund(self, request: RefundRequest) -> RefundResponse:
        """Processa um estorno de pagamento com tracing OpenTelemetry."""
        import time
        from decimal import Decimal
        start_time = time.time()

        with tracer.start_as_current_span("payment.refund") as span:
            span.set_attribute("refund.transaction_id", request.transaction_id)
            span.set_attribute("refund.amount", float(request.amount) if request.amount else 0)
            span.set_attribute("refund.reason", request.reason or "")

            if not self.sdk:
                span.set_attribute("refund.success", False)
                span.set_attribute("refund.error", "SDK not configured")
                return RefundResponse(
                    success=False,
                    transaction_id=request.transaction_id,
                    message="Serviço de Pagamento não configurado",
                    status="error"
                )

            try:
                # Verificar se é um ID simulado (MOCK-)
                if request.transaction_id.startswith("MOCK-"):
                    logger.info("Processing mock refund",
                               transaction_id=request.transaction_id,
                               amount=float(request.amount) if request.amount else "total")
                    return self._mock_refund_response(request, success=True,
                                                       message="Estorno simulado processado com sucesso")

                # Processar estorno real via Mercado Pago
                refund_data = {}
                if request.amount:
                    refund_data["amount"] = float(request.amount)

                logger.info("Processing refund via Mercado Pago",
                           transaction_id=request.transaction_id,
                           amount=float(request.amount) if request.amount else "total")

                # Chamar API de estorno do Mercado Pago
                refund_response = self.sdk.refund().create(
                    request.transaction_id,
                    refund_data
                )

                response = refund_response.get("response", {})
                status_code = refund_response.get("status", 500)

                if status_code in [200, 201]:
                    refund_id = str(response.get("id", ""))
                    amount_refunded = Decimal(str(response.get("amount", 0)))

                    span.set_attribute("refund.success", True)
                    span.set_attribute("refund.id", refund_id)

                    refund_counter.add(1, {
                        "success": "true",
                        "status": response.get("status", "approved")
                    })

                    # Flush síncrono de métricas
                    force_flush_metrics(timeout_millis=500)

                    logger.info("Refund processed successfully",
                               transaction_id=request.transaction_id,
                               refund_id=refund_id,
                               amount_refunded=float(amount_refunded))

                    return RefundResponse(
                        success=True,
                        refund_id=refund_id,
                        transaction_id=request.transaction_id,
                        message="Estorno processado com sucesso",
                        status=response.get("status", "approved"),
                        amount_refunded=amount_refunded
                    )
                else:
                    error_message = response.get("message", "Erro ao processar estorno")
                    span.set_attribute("refund.success", False)
                    span.set_attribute("refund.error", error_message)

                    refund_counter.add(1, {
                        "success": "false",
                        "status": "error"
                    })

                    # Flush síncrono de métricas
                    force_flush_metrics(timeout_millis=500)

                    logger.error("Refund failed",
                                transaction_id=request.transaction_id,
                                error=error_message,
                                status_code=status_code)

                    return RefundResponse(
                        success=False,
                        transaction_id=request.transaction_id,
                        message=error_message,
                        status="error"
                    )

            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)

                refund_counter.add(1, {
                    "success": "false",
                    "status": "exception"
                })

                # Flush síncrono de métricas
                force_flush_metrics(timeout_millis=500)

                logger.exception("Refund processing failed",
                               transaction_id=request.transaction_id,
                               error=str(e))

                return RefundResponse(
                    success=False,
                    transaction_id=request.transaction_id,
                    message=f"Erro ao processar estorno: {str(e)}",
                    status="error"
                )

    def _mock_refund_response(self, request: RefundRequest, success: bool, message: str) -> RefundResponse:
        """Resposta simulada para estornos de transações MOCK."""
        from decimal import Decimal
        return RefundResponse(
            success=success,
            refund_id=f"REFUND-{request.transaction_id}" if success else None,
            transaction_id=request.transaction_id,
            message=message,
            status="approved" if success else "rejected",
            amount_refunded=request.amount if success else None
        )
