"""
Configuração de OpenTelemetry para Oficina Pro Payments.

Tech Challenge FIAP - Observabilidade
Envia Traces, Métricas e Logs para New Relic via OTLP.
"""

import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.metrics.view import View
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator

logger = logging.getLogger(__name__)


def setup_telemetry(app=None):
    """
    Configura OpenTelemetry completo com exportação para New Relic.

    Args:
        app: Instância FastAPI para instrumentação automática
    """
    # Verificar se telemetria está habilitada
    telemetry_enabled = os.getenv("TELEMETRY_ENABLED", "true").lower() == "true"
    if not telemetry_enabled:
        logger.info("Telemetry disabled via TELEMETRY_ENABLED=false")
        return

    # Configurações
    service_name = os.getenv("OTEL_SERVICE_NAME", "oficinapro-payments")
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")
    environment = os.getenv("ENVIRONMENT", "production")

    # New Relic OTLP endpoint
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://otlp.nr-data.net")
    new_relic_key = os.getenv("NEW_RELIC_LICENSE_KEY", "")

    if not new_relic_key:
        logger.warning("NEW_RELIC_LICENSE_KEY not set, telemetry will not be exported")
        return

    # Headers para autenticação New Relic
    headers = {"api-key": new_relic_key}

    # 1. Criar Resource com atributos do serviço
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        DEPLOYMENT_ENVIRONMENT: environment,
        "cloud.provider": "aws",
        "cloud.platform": "kubernetes",
        "telemetry.sdk.language": "python",
        "telemetry.sdk.name": "opentelemetry",
    })

    # 2. Configurar Trace Provider
    trace_exporter = OTLPSpanExporter(
        endpoint=f"{otlp_endpoint}/v1/traces",
        headers=headers,
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)

    # 3. Configurar Metric Provider com flush manual/síncrono
    metric_exporter = OTLPMetricExporter(
        endpoint=f"{otlp_endpoint}/v1/metrics",
        headers=headers,
    )

    # Usar PeriodicReader com intervalo curto (1s) para comportamento quasi-síncrono
    # Isso garante que métricas sejam enviadas rapidamente sem bloquear requests
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=1000,  # Export a cada 1s (quasi-síncrono)
    )

    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    logger.info("Metrics configured with 1s interval for near real-time export")

    # 4. Configurar Propagators (W3C Trace Context + Baggage)
    set_global_textmap(CompositePropagator([
        TraceContextTextMapPropagator(),
        W3CBaggagePropagator(),
    ]))

    # 5. Instrumentar bibliotecas automaticamente
    # Instrumentar logging para adicionar trace_id aos logs
    LoggingInstrumentor().instrument(set_logging_format=True)

    # Instrumentar requests HTTP
    RequestsInstrumentor().instrument()

    # Instrumentar FastAPI se app foi passado
    if app:
        FastAPIInstrumentor.instrument_app(app)

    logger.info(f"OpenTelemetry configured for {service_name}",
                extra={
                    "service.name": service_name,
                    "otlp.endpoint": otlp_endpoint,
                    "environment": environment,
                })


def get_tracer(name: str = __name__):
    """Obtém um tracer para criar spans customizados."""
    return trace.get_tracer(name)


def get_meter(name: str = __name__):
    """Obtém um meter para criar métricas customizadas."""
    return metrics.get_meter(name)


def force_flush_metrics(timeout_millis: int = 1000):
    """
    Força o flush de métricas pendentes de forma síncrona.
    Útil para garantir que métricas sejam enviadas imediatamente após operações críticas.

    Args:
        timeout_millis: Timeout em milissegundos para o flush

    Returns:
        bool: True se flush foi bem-sucedido, False caso contrário
    """
    try:
        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, 'force_flush'):
            result = meter_provider.force_flush(timeout_millis=timeout_millis)
            logger.debug(f"Manual metrics flush completed: {result}")
            return result
        return False
    except Exception as e:
        logger.warning(f"Error during manual metrics flush: {e}")
        return False


def shutdown_telemetry():
    """
    Encerra providers de telemetria com flush de dados pendentes.
    Garante que traces e métricas sejam enviados antes do shutdown.
    """
    logger.info("Shutting down telemetry providers...")

    # Shutdown tracer provider (flush pending spans)
    tracer_provider = trace.get_tracer_provider()
    if hasattr(tracer_provider, 'force_flush'):
        try:
            tracer_provider.force_flush(timeout_millis=2000)  # 2 segundos para flush
            logger.debug("Tracer provider flushed successfully")
        except Exception as e:
            logger.warning(f"Error flushing tracer provider: {e}")

    if hasattr(tracer_provider, 'shutdown'):
        try:
            tracer_provider.shutdown()
            logger.debug("Tracer provider shutdown successfully")
        except Exception as e:
            logger.warning(f"Error shutting down tracer provider: {e}")

    # Shutdown meter provider (flush pending metrics)
    meter_provider = metrics.get_meter_provider()
    if hasattr(meter_provider, 'force_flush'):
        try:
            meter_provider.force_flush(timeout_millis=2000)  # 2 segundos para flush
            logger.debug("Meter provider flushed successfully")
        except Exception as e:
            logger.warning(f"Error flushing meter provider: {e}")

    if hasattr(meter_provider, 'shutdown'):
        try:
            meter_provider.shutdown()
            logger.debug("Meter provider shutdown successfully")
        except Exception as e:
            logger.warning(f"Error shutting down meter provider: {e}")

    logger.info("Telemetry shutdown completed")

