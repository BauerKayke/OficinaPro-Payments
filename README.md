# 💳 OficinaPro - Payment API

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Mercado Pago](https://img.shields.io/badge/Mercado%20Pago-SDK-00B1EA)](https://www.mercadopago.com.br/developers/)
[![License](https://img.shields.io/badge/License-Academic-blue)](LICENSE)

## 📋 Descrição

API de Pagamentos do projeto OficinaPro, responsável por processar transações financeiras através da integração com o **Mercado Pago**. Desenvolvida em Python com FastAPI, suporta múltiplos métodos de pagamento: PIX, Boleto, Cartão de Crédito e Débito.

## 🎯 Propósito

- Processar pagamentos de ordens de serviço
- Integrar com gateway de pagamento Mercado Pago
- Gerar QR Codes PIX e links de pagamento
- Fornecer status de transações em tempo real
- Webhook para confirmação automática de pagamentos

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Descrição |
|------------|--------|-----------|
| **Python** | 3.11+ | Linguagem de programação |
| **FastAPI** | 0.100+ | Framework web assíncrono |
| **Mercado Pago SDK** | 2.x | Integração com gateway de pagamento |
| **Pydantic** | 2.x | Validação de dados |
| **Uvicorn** | - | ASGI Server |
| **Docker** | - | Containerização (AMD64/x86_64) |
| **OpenTelemetry** | 1.22+ | Observabilidade (Traces, Metrics, Logs) |
| **New Relic** | - | APM e Monitoring |
| **AWS SQS** | - | Mensageria assíncrona (opcional) |
| **Kubernetes (K3s)** | 1.28+ | Orquestração de containers |

## 📁 Estrutura do Repositório

```
OficinaPro-Payments/
├── app/
│   ├── main.py              # Entrypoint da aplicação
│   ├── schemas.py           # Schemas Pydantic (DTOs)
│   ├── logging_config.py    # Configuração de logs estruturados
│   ├── telemetry.py         # Configuração OpenTelemetry
│   ├── metrics.py           # Métricas customizadas
│   ├── routers/
│   │   └── api.py           # Rotas da API
│   ├── services/
│   │   └── payment_service.py  # Lógica de integração com MP
│   └── messaging/           # (Opcional) SQS Consumer
│       └── sqs_consumer.py
├── deployment/
│   └── kubernetes/
│       ├── payment-deployment.yaml
│       └── ingress.yaml
├── Dockerfile               # Multi-stage build para AMD64
├── requirements.txt         # Dependências Python
├── test_manual.py           # Script de testes manuais
├── INTEGRATION_GUIDE.md     # Guia de integração
└── README.md
```

## 🏗️ Arquitetura do Serviço

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PAYMENT API - ARQUITETURA                            │
│                                                                              │
│   ┌────────────────┐                                                        │
│   │  Core Service  │                                                        │
│   │    (Java)      │                                                        │
│   └───────┬────────┘                                                        │
│           │                                                                  │
│           │ HTTP/JSON                                                        │
│           ▼                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        PAYMENT API (FastAPI)                         │   │
│   │                                                                      │   │
│   │   ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐    │   │
│   │   │   Routers   │───>│    Schemas      │───>│   Services      │    │   │
│   │   │   (API)     │    │   (Pydantic)    │    │ (Payment Logic) │    │   │
│   │   └─────────────┘    └─────────────────┘    └────────┬────────┘    │   │
│   │                                                      │              │   │
│   └──────────────────────────────────────────────────────┼──────────────┘   │
│                                                          │                   │
│                                                          │ SDK               │
│                                                          ▼                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     MERCADO PAGO EXTERNAL API                        │   │
│   │                                                                      │   │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│   │   │     PIX     │  │   Boleto    │  │   Crédito   │  │  Débito   │  │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Passos para Execução

### Pré-requisitos

- Docker (recomendado) ou Python 3.11+
- Token de acesso do Mercado Pago (sandbox ou produção)

### Variáveis de Ambiente

```bash
# Mercado Pago (Obrigatório)
MP_ACCESS_TOKEN=TEST-8722319752573550-123009-xxx  # Token de acesso MP

# Observabilidade (OpenTelemetry → New Relic)
TELEMETRY_ENABLED=true
OTEL_SERVICE_NAME=oficinapro-payments
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp.nr-data.net:4318
NEW_RELIC_LICENSE_KEY=your_license_key

# Aplicação
ENVIRONMENT=production
LOG_LEVEL=INFO
SERVICE_VERSION=1.0.0
PORT=8000

# SQS Consumer (Opcional - para modo dual)
ENABLE_SQS_CONSUMER=false
SQS_PAYMENT_COMMANDS_QUEUE=payment-commands-queue
AWS_REGION=us-east-1
```

### Executando com Docker (Recomendado)

```bash
# 1. Construir imagem (IMPORTANTE: especificar plataforma AMD64 para deploy em AWS)
docker build --platform linux/amd64 -t payment-api:latest .

# 2. Executar container localmente
docker run -p 8000:8000 \
  -e MP_ACCESS_TOKEN=seu_token \
  -e TELEMETRY_ENABLED=true \
  -e NEW_RELIC_LICENSE_KEY=your_key \
  payment-api:latest
```

**Nota Importante:** Ao buildar para deploy em AWS EC2/K3s (x86_64), **sempre** use `--platform linux/amd64`, mesmo em Mac M1/M2 (ARM64).

### Executando Localmente

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar aplicação
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Endpoints da API

### Health Check

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-06T10:30:00Z"
}
```

### Criar Pagamento

```http
POST /api/v1/payments
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

#### PIX

```json
{
  "order_id": "OS-2024-0001",
  "amount": 500.00,
  "method": "pix",
  "payer_email": "cliente@email.com"
}
```

**Response:**
```json
{
  "id": "123456789",
  "status": "pending",
  "method": "pix",
  "qr_code": "00020126580014br.gov.bcb.pix...",
  "qr_code_base64": "data:image/png;base64,...",
  "copy_paste": "00020126580014br.gov.bcb.pix..."
}
```

#### Boleto

```json
{
  "order_id": "OS-2024-0001",
  "amount": 500.00,
  "method": "boleto",
  "payer_email": "cliente@email.com",
  "address": {
    "zip_code": "01310100",
    "street_name": "Av. Paulista",
    "street_number": "1000",
    "neighborhood": "Bela Vista",
    "city": "São Paulo",
    "federal_unit": "SP"
  }
}
```

#### Cartão de Crédito

```json
{
  "order_id": "OS-2024-0001",
  "amount": 500.00,
  "method": "credit_card",
  "payer_email": "cliente@email.com",
  "installments": 3,
  "card_data": {
    "token": "card_token_from_frontend"
  }
}
```

### Consultar Status

```http
GET /api/v1/payments/{payment_id}
Authorization: Bearer <jwt_token>
```

## 📚 Documentação Interativa

Quando a aplicação está rodando:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔐 Segurança

| Aspecto | Implementação |
|---------|---------------|
| Autenticação | JWT Bearer Token |
| Validação | Pydantic schemas |
| HTTPS | Obrigatório em produção |
| Secrets | Variáveis de ambiente |
| Rate Limiting | Via API Gateway/Ingress |

## 🧪 Testes

### Teste Manual

```bash
# Testar PIX, Boleto, Crédito e Débito
python test_manual.py
```

### Exemplo de Teste (curl)

```bash
# PIX
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "OS-TEST-001",
    "amount": 100.00,
    "method": "pix",
    "payer_email": "test@test.com"
  }'
```

## 🔄 Integração com Core Service

O Core Domain Service (Java) integra com esta API para processar pagamentos:

```java
@Service
public class PaymentIntegrationService {

    @Value("${payment.api.url}")
    private String paymentApiUrl;

    public PaymentResponse createPayment(PaymentRequest request) {
        return restTemplate.postForObject(
            paymentApiUrl + "/api/v1/payments",
            request,
            PaymentResponse.class
        );
    }
}
```

## 📦 Deploy (Kubernetes/K3s)

### Deploy Automático via GitHub Actions

O repositório possui um pipeline CI/CD que automatiza build e deploy:

```yaml
# .github/workflows/deploy-payment-service.yml
on:
  push:
    branches: [main, feature/payments-metrics]
  workflow_dispatch:

jobs:
  build-and-deploy:
    - Login no ECR
    - Build da imagem Docker (AMD64)
    - Push para ECR
    - Deploy no K3s via kubectl
```

**Trigger:** Push para `main` ou `feature/payments-metrics`, ou manualmente via GitHub Actions UI.

### Deploy Manual

```bash
# 1. Build e push para ECR
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="315974965680"
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Login
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}

# Build (AMD64!)
docker build --platform linux/amd64 -t payment-api:latest .

# Tag e Push
docker tag payment-api:latest ${ECR_REPO}/payment-api:latest
docker push ${ECR_REPO}/payment-api:latest

# 2. Deploy no K3s
export KUBECONFIG=/path/to/k3s-config.yaml

# Criar secrets (se ainda não existirem)
kubectl create secret generic oficinapro-secrets \
  --from-literal=MP_TOKEN='TEST-xxx' \
  --from-literal=NEW_RELIC_LICENSE_KEY='your_key' \
  --namespace=oficinapro

# Aplicar deployment
kubectl apply -f deployment/kubernetes/payment-deployment.yaml

# Verificar status
kubectl get pods -n oficinapro -l app=payment-api
kubectl logs -f deployment/payment-api -n oficinapro
```

### Configuração do Deployment

O deployment K3s inclui:
- **1 réplica** (pode escalar via HPA)
- **ImagePullPolicy**: Always (para puxar última versão)
- **Resources**: Limits e requests configurados
- **Probes**: Liveness e Readiness para `/health`
- **Secrets**: ECR credentials, MP Token, New Relic Key
- **Service**: ClusterIP na porta 8000

### Expor via LoadBalancer (Opcional)

```bash
kubectl patch svc payment-service -n oficinapro -p '{"spec":{"type":"LoadBalancer"}}'
kubectl get svc payment-service -n oficinapro -w
```

## 📊 Observabilidade e Monitoramento

### OpenTelemetry Integration

O Payment API possui observabilidade completa via **OpenTelemetry**, exportando dados para **New Relic**:

#### Traces (Distributed Tracing)
- Rastreamento automático de todas as requisições HTTP
- Spans customizados para operações críticas (Mercado Pago API calls)
- Propagação de contexto (W3C Trace Context + Baggage)

#### Metrics
- **Export Interval**: 1 segundo (near real-time)
- Métricas HTTP automáticas (latência, status codes, throughput)
- Métricas customizadas de negócio (pagamentos por método, falhas, etc.)

#### Logs Estruturados (JSON)
- Logs correlacionados com `trace_id` e `span_id`
- Formato JSON para fácil indexação
- Níveis de log configuráveis via `LOG_LEVEL`

```json
{
  "@timestamp": "2026-02-12T02:30:00Z",
  "level": "INFO",
  "message": "Payment created successfully",
  "service.name": "oficinapro-payments",
  "trace.id": "abc123",
  "span.id": "def456",
  "payment_id": "123456789",
  "method": "pix",
  "amount": 500.00
}
```

### Arquitetura de Observabilidade

```
┌─────────────────────────────────────────────────────────────────┐
│                      PAYMENT API                                 │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  FastAPI App + OpenTelemetry Instrumentation             │  │
│   │                                                           │  │
│   │  • FastAPIInstrumentor (auto-instrument)                 │  │
│   │  • RequestsInstrumentor (MP SDK calls)                   │  │
│   │  • LoggingInstrumentor (trace correlation)               │  │
│   └────────────────┬─────────────────────────────────────────┘  │
│                    │                                             │
│                    │ OTLP/HTTP                                   │
│                    ▼                                             │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  OTLP Exporters                                          │  │
│   │  • Traces → https://otlp.nr-data.net:4318/v1/traces     │  │
│   │  • Metrics → https://otlp.nr-data.net:4318/v1/metrics   │  │
│   │  • Logs → (via trace correlation)                       │  │
│   └────────────────┬─────────────────────────────────────────┘  │
└────────────────────┼──────────────────────────────────────────────┘
                     │
                     │ HTTPS + API Key
                     ▼
        ┌────────────────────────────────┐
        │       NEW RELIC APM            │
        │                                │
        │  • Distributed Tracing         │
        │  • Service Maps                │
        │  • Dashboards                  │
        │  • Alerts                      │
        │  • Logs (correlated)           │
        └────────────────────────────────┘
```

### Dashboards e Alertas

No **New Relic**, você pode visualizar:

1. **Service Overview**:
   - Throughput (requests/minute)
   - Response time (p50, p95, p99)
   - Error rate
   - Apdex score

2. **Distributed Tracing**:
   - Trace waterfall (Payment API → Mercado Pago)
   - Latency breakdown por operação
   - Error traces com stack completo

3. **Logs Correlacionados**:
   - Logs vinculados a traces específicos
   - Busca por `payment_id`, `method`, `amount`
   - Filtros por erro/sucesso

### Ativar/Desativar Telemetria

```bash
# Desativar (para debug local ou reduzir overhead)
export TELEMETRY_ENABLED=false

# Ativar (produção)
export TELEMETRY_ENABLED=true
```

**Overhead**: ~5-10ms de latência adicional por request (aceitável para produção).

## 🔄 Modo Dual: HTTP API + SQS Consumer

O Payment API pode operar em **dois modos simultaneamente**:

### 1. HTTP API (Síncrono)
- Endpoints REST para criação e consulta de pagamentos
- Respostas imediatas para o client

### 2. SQS Consumer (Assíncrono)
- Thread em background consumindo mensagens SQS
- Long-polling (20s wait time) para eficiência
- Processa comandos de pagamento via fila

```python
# app/main.py
if os.getenv('ENABLE_SQS_CONSUMER', 'true').lower() == 'true':
    sqs_consumer = SQSPaymentConsumer()
    consumer_thread = threading.Thread(
        target=sqs_consumer.start_consuming,
        daemon=True
    )
    consumer_thread.start()
```

**Decisão Arquitetural:** Por ter o SQS consumer embarcado (long-running thread), o Payment API é **ideal para K3s**, não para AWS Lambda (que tem timeout de 15 minutos).

Ver [ANALISE_DEPLOYMENT_PAYMENTS.md](/Users/kbmarins/Desktop/Personal/FIAP/ANALISE_DEPLOYMENT_PAYMENTS.md) para análise completa.

## 📊 Métodos de Pagamento Suportados

| Método | Status | Tempo Confirmação |
|--------|--------|-------------------|
| **PIX** | ✅ Implementado | Instantâneo |
| **Boleto** | ✅ Implementado | 1-3 dias úteis |
| **Crédito** | ✅ Implementado | Instantâneo |
| **Débito** | ✅ Implementado | Instantâneo |

## 📚 Documentação Relacionada

| Documento | Descrição |
|-----------|-----------|
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | Guia completo de integração |
| [Core Service](../core-domain-service/README.md) | Aplicação principal |
| [Arquitetura Geral](../core-domain-service/docs/INDEX.md) | Documentação arquitetural |
| [Mercado Pago Docs](https://www.mercadopago.com.br/developers/) | Documentação oficial MP |

## 💰 Custos

- **Mercado Pago**: Taxa por transação (varia por método)
- **Infraestrutura**: Incluído no Free Tier AWS (K8s)
- **API**: Sem custos adicionais
- **New Relic**: Free tier com 100GB/mês de ingestão de dados

## 🐛 Troubleshooting

### Erro: `exec format error`

**Causa:** Imagem Docker buildada em Mac M1/M2 (ARM64) tentando rodar em servidor AMD64.

**Solução:**
```bash
docker build --platform linux/amd64 -t payment-api:latest .
```

### Erro: `RuntimeError: Cannot add middleware after an application has started`

**Causa:** `FastAPIInstrumentor.instrument_app()` sendo chamado dentro do `lifespan`.

**Solução:** Verificar que `setup_telemetry(app)` está sendo chamado **após** a criação do app, mas **antes** de qualquer middleware ou rota.

```python
# ✅ Correto
app = FastAPI(lifespan=lifespan)
setup_telemetry(app)

# ❌ Errado
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry(app)  # Muito tarde!
```

### Pods em `ImagePullBackOff`

**Causa:** Falha ao puxar imagem do ECR (credenciais ou secret incorreto).

**Solução:**
```bash
# Verificar se ecr-secret existe
kubectl get secret ecr-secret -n oficinapro

# Recriar se necessário
kubectl delete secret ecr-secret -n oficinapro
kubectl create secret docker-registry ecr-secret \
  --docker-server=315974965680.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password="$(aws ecr get-login-password --region us-east-1)" \
  --namespace=oficinapro
```

### Health Check Failing

**Verificar:**
```bash
# Logs do pod
kubectl logs -f deployment/payment-api -n oficinapro

# Exec no pod e testar localmente
kubectl exec -it <pod-name> -n oficinapro -- wget -qO- http://localhost:8000/health
```

### SQS Consumer Não Consome Mensagens

**Verificar:**
1. `ENABLE_SQS_CONSUMER=true` está configurado
2. Fila SQS existe e tem mensagens
3. IAM role/credentials têm permissão `sqs:ReceiveMessage`, `sqs:DeleteMessage`
4. Logs: `kubectl logs <pod> -n oficinapro | grep SQS`

## 👥 Equipe

Desenvolvido para o **Tech Challenge da FIAP**.

---

**Status**: ✅ Produção Ready - Deployed no K3s AWS  
**CI/CD**: ✅ GitHub Actions Automatizado  
**Observabilidade**: ✅ OpenTelemetry → New Relic  
**Swagger**: http://localhost:8000/docs  
**Última atualização**: Fevereiro de 2026
