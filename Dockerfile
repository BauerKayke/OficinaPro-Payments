FROM python:3.11-slim

# Metadados
LABEL maintainer="FIAP Tech Challenge"
LABEL description="OficinaPro Payment Service - Microserviço de Pagamentos"
LABEL version="1.0.0"

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para melhor cache de layers)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app/ ./app/

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicialização com 2 workers para melhor performance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
