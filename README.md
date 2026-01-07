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
| **Docker** | - | Containerização |

## 📁 Estrutura do Repositório

```
OficinaPro-Payments/
├── app/
│   ├── main.py              # Entrypoint da aplicação
│   ├── schemas.py           # Schemas Pydantic (DTOs)
│   ├── routers/
│   │   └── api.py           # Rotas da API
│   └── services/
│       └── payment_service.py  # Lógica de integração com MP
├── deployment/
│   └── kubernetes/
│       ├── payment-deployment.yaml
│       └── ingress.yaml
├── Dockerfile
├── requirements.txt
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
# Obrigatório
MP_ACCESS_TOKEN=seu_token_mercado_pago

# Opcionais
PORT=8000
DEBUG=true
```

### Executando com Docker (Recomendado)

```bash
# 1. Construir imagem
docker build -t payment-api .

# 2. Executar container
docker run -p 8000:8000 \
  -e MP_ACCESS_TOKEN=seu_token \
  payment-api
```

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

## 📦 Deploy (Kubernetes)

```bash
# Aplicar manifests
kubectl apply -f deployment/kubernetes/

# Verificar pods
kubectl get pods -l app=payment-api
```

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

## 👥 Equipe

Desenvolvido para o **Tech Challenge da FIAP**.

---

**Status**: ✅ Produção Ready
**Swagger**: http://localhost:8000/docs
**Última atualização**: Janeiro de 2026
