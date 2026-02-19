"""
Métricas Customizadas para Oficina Pro Payments.

Tech Challenge FIAP - Observabilidade
Define métricas de negócio para monitoramento de pagamentos.
"""

from opentelemetry import metrics
from app.telemetry import get_meter

# Obter meter para criar métricas
meter = get_meter("oficinapro.payments.metrics")

# Contador: Total de tentativas de processamento de pagamento
payment_attempts_counter = meter.create_counter(
    name="payment.attempts",
    description="Total number of payment processing attempts",
    unit="1",
)

# Contador: Pagamentos bem-sucedidos
payment_success_counter = meter.create_counter(
    name="payment.success",
    description="Total number of successful payments",
    unit="1",
)

# Contador: Pagamentos falhados
payment_failure_counter = meter.create_counter(
    name="payment.failure",
    description="Total number of failed payments",
    unit="1",
)

# Histograma: Duração do processamento de pagamento
payment_duration_histogram = meter.create_histogram(
    name="payment.duration",
    description="Duration of payment processing in milliseconds",
    unit="ms",
)

# Histograma: Valor dos pagamentos processados
payment_amount_histogram = meter.create_histogram(
    name="payment.amount",
    description="Payment amount in BRL",
    unit="BRL",
)

# Contador: Integrações com Mercado Pago
mercadopago_api_calls_counter = meter.create_counter(
    name="mercadopago.api.calls",
    description="Total number of Mercado Pago API calls",
    unit="1",
)

# Contador: Erros de integração com Mercado Pago
mercadopago_api_errors_counter = meter.create_counter(
    name="mercadopago.api.errors",
    description="Total number of Mercado Pago API errors",
    unit="1",
)


def record_payment_attempt(payment_method: str, order_id: int):
    """Registra uma tentativa de processamento de pagamento."""
    payment_attempts_counter.add(
        1,
        attributes={
            "payment_method": payment_method,
            "order_id": str(order_id),
        }
    )


def record_payment_success(payment_method: str, order_id: int, amount: float, duration_ms: float):
    """Registra um pagamento bem-sucedido."""
    payment_success_counter.add(
        1,
        attributes={
            "payment_method": payment_method,
            "order_id": str(order_id),
        }
    )

    payment_amount_histogram.record(
        amount,
        attributes={
            "payment_method": payment_method,
            "status": "success",
        }
    )

    payment_duration_histogram.record(
        duration_ms,
        attributes={
            "payment_method": payment_method,
            "status": "success",
        }
    )


def record_payment_failure(payment_method: str, order_id: int, error_type: str, duration_ms: float):
    """Registra uma falha de pagamento."""
    payment_failure_counter.add(
        1,
        attributes={
            "payment_method": payment_method,
            "order_id": str(order_id),
            "error_type": error_type,
        }
    )

    payment_duration_histogram.record(
        duration_ms,
        attributes={
            "payment_method": payment_method,
            "status": "failure",
            "error_type": error_type,
        }
    )


def record_mercadopago_api_call(endpoint: str, method: str):
    """Registra uma chamada à API do Mercado Pago."""
    mercadopago_api_calls_counter.add(
        1,
        attributes={
            "endpoint": endpoint,
            "method": method,
        }
    )


def record_mercadopago_api_error(endpoint: str, method: str, error_type: str):
    """Registra um erro na API do Mercado Pago."""
    mercadopago_api_errors_counter.add(
        1,
        attributes={
            "endpoint": endpoint,
            "method": method,
            "error_type": error_type,
        }
    )
