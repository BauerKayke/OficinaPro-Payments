import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    print("Testing /health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Failed: {e}")

def test_pix_payment():
    print("\nTesting PIX Payment...")
    payload = {
        "order_id": 12345,
        "amount": 150.00,
        "method": "PIX",
        "description": "Service Order #12345",
        "payer_email": "test_user_1234@test.com",
        "payer_cpf": "19119119100"
    }
    try:
        response = requests.post(f"{BASE_URL}/payments", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Failed: {e}")

def test_boleto_payment():
    print("\nTesting Boleto Payment...")
    payload = {
        "order_id": 12346,
        "amount": 200.50,
        "method": "BOLETO",
        "description": "Service Order #12346",
        "payer_email": "test_user_1234@test.com",
        "payer_cpf": "19119119100"
    }
    try:
        response = requests.post(f"{BASE_URL}/payments", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Failed: {e}")

def test_credit_card_payment():
    print("\nTesting Credit Card Payment...")
    payload = {
        "order_id": 12347,
        "amount": 300.75,
        "method": "CARTAO_CREDITO",
        "description": "Service Order #12347",
        "payer_email": "test_user_1234@test.com",
        "card_data": {
            "card_number": "1234567890123456",
            "cardholder_name": "TEST USER",
            "expiration_date": "12/30",
            "security_code": "123",
            "installments": 2
        }
    }
    try:
        response = requests.post(f"{BASE_URL}/payments", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Failed: {e}")

def test_debit_card_payment():
    print("\nTesting Debit Card Payment...")
    payload = {
        "order_id": 12348,
        "amount": 50.25,
        "method": "CARTAO_DEBITO",
        "description": "Service Order #12348",
        "payer_email": "test_user_1234@test.com",
        "card_data": {
            "card_number": "1234567890123456",
            "cardholder_name": "TEST USER",
            "expiration_date": "12/30",
            "security_code": "123",
            "installments": 1
        }
    }
    try:
        response = requests.post(f"{BASE_URL}/payments", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_health()
    test_pix_payment()
    test_boleto_payment()
    test_credit_card_payment()
    test_debit_card_payment()
