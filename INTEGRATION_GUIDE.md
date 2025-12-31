# Integration Guide: OficinaPro (Java) -> Payment API (Python)

This guide details how to connect the existing `OficinaPro` Spring Boot application to the new `Payment API`.

## Architecture
The `OficinaPro` (Java) will act as a client, sending payment requests to the `Payment API` (Python) via HTTP REST calls.

## Steps

### 1. Infrastructure (Docker Compose)
Ensure both services runs on the same network. Add the Python API to your `docker-compose.yml` (if it exists) or run them sharing a network.

**Example `docker-compose.yml` addition:**
```yaml
  payment-api:
    build: ./Payment-API
    ports:
      - "8000:8000"
    environment:
      - MP_ACCESS_TOKEN=${MP_ACCESS_TOKEN}
    networks:
      - oficinapro-network
```

### 2. Java Configuration
Add the Payment API URL to your `src/main/resources/application.yml` or `application.properties`.

```properties
app.payment-api.url=http://payment-api:8000/api/v1
```

### 3. Refactoring `PaymentGatewayAdapter.java`

You need to modify `br.com.oficinapro.coredomainservice.infrastructure.gateway.PaymentGatewayAdapter`.

**Dependencies**: Ensure you have `RestTemplate` or `OpenFeign` available. Assuming `RestTemplate`.

#### Example Implementation Logic

```java
@Component
@RequiredArgsConstructor
public class PaymentGatewayAdapter implements PaymentGatewayPort {

    private final RestTemplate restTemplate;
    
    @Value("${app.payment-api.url}")
    private String paymentApiUrl;

    @Override
    public PaymentResult processarPagamentoPix(Long ordemServicoId, BigDecimal valor, String chavePix) {
        // 1. Build Payload
        Map<String, Object> payload = new HashMap<>();
        payload.put("order_id", ordemServicoId);
        payload.put("amount", valor);
        payload.put("method", "PIX");
        payload.put("description", "Order " + ordemServicoId);
        payload.put("payer_email", "customer@email.com"); // Pass real email
        payload.put("payer_cpf", "12345678900"); // Pass real CPF

        // 2. Call Python API
        try {
            ResponseEntity<PaymentResponseDTO> response = restTemplate.postForEntity(
                paymentApiUrl + "/payments", 
                payload, 
                PaymentResponseDTO.class
            );
            
            // 3. Map Response
            if (response.getBody() != null && response.getBody().isSuccess()) {
                return new PaymentResult(
                    true, 
                    response.getBody().getTransactionId(),
                    "PIX Created",
                    PaymentStatus.PENDENTE,
                    null, 
                    response.getBody().getQrCode()
                );
            }
        } catch (Exception e) {
            log.error("Error calling Payment API", e);
        }
        return new PaymentResult(false, ...); // Handle Error
    }
}
```

### 4. Create DTOs in Java
You will need a Java class to represent the JSON response from Python.

```java
@Data
public class PaymentResponseDTO {
    private boolean success;
    @JsonProperty("transaction_id")
    private String transactionId;
    private String message;
    private String status;
    @JsonProperty("qr_code")
    private String qrCode;
    @JsonProperty("ticket_url")
    private String ticketUrl;
}
```

## Checklist
- [ ] Add `Payment-API` to Docker Compose.
- [ ] Configure `app.payment-api.url` in Java.
- [ ] Create `PaymentResponseDTO` in Java.
- [ ] Inject `RestTemplate` in `PaymentGatewayAdapter`.
- [ ] Replace mock logic with `restTemplate.postForEntity(...)` calls.
