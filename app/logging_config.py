"""
Configuração de Logging Estruturado JSON para Oficina Pro Payments.

Tech Challenge FIAP - Observabilidade
Implementa logs estruturados em JSON para integração com sistemas de observabilidade.
"""

import logging
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """
    Formatter que produz logs em JSON estruturado.
    Compatível com New Relic, ELK Stack, CloudWatch, etc.
    """

    def __init__(
        self,
        service_name: str = "oficinapro-payments",
        service_version: str = "1.0.0",
        environment: str = "production"
    ):
        super().__init__()
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """Formata o log record como JSON estruturado."""
        log_entry: Dict[str, Any] = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service.name": self.service_name,
            "service.version": self.service_version,
            "environment": self.environment,
            "logger.name": record.name,
            "thread.name": record.threadName,
            "process.pid": record.process,
        }

        # Adicionar trace context se disponível (OpenTelemetry)
        trace_id = getattr(record, 'otelTraceID', None)
        span_id = getattr(record, 'otelSpanID', None)
        if trace_id:
            log_entry["trace.id"] = trace_id
        if span_id:
            log_entry["span.id"] = span_id

        # Adicionar campos extras do record
        if hasattr(record, 'extra_fields') and record.extra_fields:
            log_entry["fields"] = record.extra_fields

        # Adicionar informações de exceção se presente
        if record.exc_info:
            log_entry["error.type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            log_entry["error.message"] = str(record.exc_info[1]) if record.exc_info[1] else None
            log_entry["error.stack_trace"] = ''.join(traceback.format_exception(*record.exc_info))

        # Adicionar localização do código
        if record.pathname:
            log_entry["code.filepath"] = record.pathname
            log_entry["code.lineno"] = record.lineno
            log_entry["code.function"] = record.funcName

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class StructuredLogger:
    """
    Logger estruturado que suporta campos extras para contexto de negócio.
    """

    def __init__(self, name: str, logger: logging.Logger):
        self._name = name
        self._logger = logger

    def _log(self, level: int, msg: str, extra_fields: Optional[Dict[str, Any]] = None, exc_info=None):
        """Método interno para log com campos extras."""
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        self._logger.log(level, msg, extra=extra, exc_info=exc_info)

    def debug(self, msg: str, **kwargs):
        """Log de debug com campos opcionais."""
        self._log(logging.DEBUG, msg, kwargs if kwargs else None)

    def info(self, msg: str, **kwargs):
        """Log informativo com campos opcionais."""
        self._log(logging.INFO, msg, kwargs if kwargs else None)

    def warning(self, msg: str, **kwargs):
        """Log de aviso com campos opcionais."""
        self._log(logging.WARNING, msg, kwargs if kwargs else None)

    def error(self, msg: str, exc_info=None, **kwargs):
        """Log de erro com campos opcionais e stack trace."""
        self._log(logging.ERROR, msg, kwargs if kwargs else None, exc_info=exc_info)

    def exception(self, msg: str, **kwargs):
        """Log de exceção com stack trace automático."""
        self._log(logging.ERROR, msg, kwargs if kwargs else None, exc_info=True)


def setup_logging(
    service_name: str = None,
    service_version: str = None,
    environment: str = None,
    level: str = None
) -> None:
    """
    Configura o logging estruturado para a aplicação.

    Args:
        service_name: Nome do serviço (default: env OTEL_SERVICE_NAME ou 'oficinapro-payments')
        service_version: Versão do serviço (default: '1.0.0')
        environment: Ambiente (default: env ENVIRONMENT ou 'production')
        level: Nível de log (default: env LOG_LEVEL ou 'INFO')
    """
    # Valores padrão com fallback para variáveis de ambiente
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "oficinapro-payments")
    service_version = service_version or os.getenv("SERVICE_VERSION", "1.0.0")
    environment = environment or os.getenv("ENVIRONMENT", "production")
    level = level or os.getenv("LOG_LEVEL", "INFO")

    # Configurar handler
    handler = logging.StreamHandler(sys.stdout)

    # Usar JSON em produção, texto em desenvolvimento
    if environment in ("production", "prod"):
        handler.setFormatter(JSONFormatter(
            service_name=service_name,
            service_version=service_version,
            environment=environment
        ))
    else:
        # Formato legível para desenvolvimento
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)-8s [%(name)s] %(message)s'
        ))

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remover handlers existentes para evitar duplicação
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)

    root_logger.addHandler(handler)

    # Reduzir verbosidade de bibliotecas externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """
    Obtém um logger estruturado para o módulo especificado.

    Args:
        name: Nome do módulo (geralmente __name__)

    Returns:
        StructuredLogger configurado
    """
    return StructuredLogger(name, logging.getLogger(name))

