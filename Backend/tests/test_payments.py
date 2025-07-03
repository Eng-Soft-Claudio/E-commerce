"""
Suíte de Testes para o recurso de Pagamentos (Payments).

Testa os endpoints sob o prefixo '/payments', cobrindo o fluxo de criação
de sessão de checkout e o processamento de webhooks do Stripe.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from fastapi.testclient import TestClient
import pytest
from typing import Dict
from unittest.mock import MagicMock

from sqlalchemy.orm import Session
import stripe

from src.models import Order

# -------------------------------------------------------------------------- #
#                        SETUP E FIXTURES AUXILIARES                         #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def order_for_payment(
    client: TestClient, user_token_headers: Dict, superuser_token_headers: Dict
) -> Dict:
    """Fixture que cria um cenário completo para o pagamento."""
    cat_resp = client.post(
        "/categories/", headers=superuser_token_headers, json={"title": "Pagamentos"}
    )
    cat_resp.raise_for_status()

    prod_data = {
        "sku": "PAG-001",
        "name": "Produto para Pagar",
        "price": 123.45,
        "stock": 10,
        "category_id": cat_resp.json()["id"],
        "weight_kg": 0.8,
        "height_cm": 10,
        "width_cm": 15,
        "length_cm": 25,
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    prod_resp.raise_for_status()

    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": prod_resp.json()["id"], "quantity": 1},
    ).raise_for_status()

    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    return order_response.json()


# -------------------------------------------------------------------------- #
#                   TESTES PARA 'create_checkout_session'                    #
# -------------------------------------------------------------------------- #


def test_create_checkout_session_success(
    client: TestClient, order_for_payment: Dict, mocker
):
    """Testa o caminho feliz da criação de uma sessão de checkout."""
    order_id = order_for_payment["id"]
    mock_stripe_session = MagicMock(
        url="https://checkout.stripe.com/pay/cs_test_12345",
        payment_intent="pi_test_12345",
    )
    mocker.patch("stripe.checkout.Session.create", return_value=mock_stripe_session)
    response = client.post(f"/payments/create-checkout-session/{order_id}")
    assert response.status_code == 200
    assert response.json() == {"checkout_url": mock_stripe_session.url}


def test_create_checkout_for_nonexistent_order(client: TestClient):
    response = client.post("/payments/create-checkout-session/9999")
    assert response.status_code == 404


def test_create_checkout_for_paid_order(
    client: TestClient, order_for_payment: Dict, db_session: Session
):
    order_id = order_for_payment["id"]
    order_in_db = db_session.get(Order, order_id)
    assert order_in_db is not None
    order_in_db.status = "paid"
    db_session.commit()
    response = client.post(f"/payments/create-checkout-session/{order_id}")
    assert response.status_code == 400


def test_create_checkout_session_handles_stripe_error(
    client: TestClient, order_for_payment: Dict, mocker
):
    order_id = order_for_payment["id"]
    mocker.patch(
        "stripe.checkout.Session.create", side_effect=stripe.StripeError("API Error")
    )
    response = client.post(f"/payments/create-checkout-session/{order_id}")
    assert response.status_code == 400
    assert "Stripe error" in response.json()["detail"]


def test_create_checkout_session_handles_missing_url(
    client: TestClient, order_for_payment: Dict, mocker
):
    order_id = order_for_payment["id"]
    mocker.patch(
        "stripe.checkout.Session.create",
        return_value=MagicMock(url=None, payment_intent="pi_test"),
    )
    response = client.post(f"/payments/create-checkout-session/{order_id}")
    assert response.status_code == 500
    assert "did not return a checkout URL" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                             TESTES PARA O WEBHOOK                          #
# -------------------------------------------------------------------------- #


def test_stripe_webhook_success_payment(
    client: TestClient, order_for_payment: Dict, db_session: Session, mocker
):
    """Testa o processamento bem-sucedido de um webhook de pagamento."""
    order_id = order_for_payment["id"]
    event_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"order_id": str(order_id)},
                "payment_intent": "pi_test_123",
                "payment_status": "paid",
            }
        },
    }
    mocker.patch("stripe.Webhook.construct_event", return_value=event_payload)
    response = client.post(
        "/payments/webhook",
        json=event_payload,
        headers={"Stripe-Signature": "dummy_sig"},
    )
    assert response.status_code == 200
    order_in_db = db_session.get(Order, order_id)
    assert order_in_db is not None
    assert order_in_db.status == "paid"
    assert order_in_db.payment_intent_id == "pi_test_123"


def test_stripe_webhook_invalid_signature(client: TestClient, mocker):
    """Testa a falha do webhook quando a assinatura do Stripe é inválida."""
    from stripe import SignatureVerificationError

    mocker.patch(
        "stripe.Webhook.construct_event",
        side_effect=SignatureVerificationError("Invalid sig", "sig"),
    )
    response = client.post(
        "/payments/webhook", json={}, headers={"Stripe-Signature": "invalid_sig"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid webhook signature"


def test_stripe_webhook_handles_value_error(client: TestClient, mocker):
    """Testa o tratamento de um payload inválido que causa ValueError."""
    mocker.patch(
        "stripe.Webhook.construct_event", side_effect=ValueError("Invalid payload")
    )
    response = client.post(
        "/payments/webhook",
        content="not-a-valid-json",
        headers={"Stripe-Signature": "dummy_sig"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid webhook payload"


def test_stripe_webhook_handles_missing_order_id(client: TestClient, mocker):
    """Testa o webhook recebendo um evento completo, mas sem order_id."""
    event_payload = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {}}},
    }
    mocker.patch("stripe.Webhook.construct_event", return_value=event_payload)
    response = client.post(
        "/payments/webhook",
        json=event_payload,
        headers={"Stripe-Signature": "dummy_sig"},
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "Webhook ignored, no order_id."


def test_stripe_webhook_handles_unhandled_event_type(client: TestClient, mocker):
    """Testa o caminho do 'else', recebendo um tipo de evento não tratado."""
    event_payload = {"type": "payment_intent.created"}
    mocker.patch("stripe.Webhook.construct_event", return_value=event_payload)
    response = client.post(
        "/payments/webhook",
        json=event_payload,
        headers={"Stripe-Signature": "dummy_sig"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success"}


def test_stripe_webhook_handles_db_update_failure(
    client: TestClient, order_for_payment: Dict, db_session: Session, mocker
):
    """Testa o tratamento de uma falha de banco de dados durante o processamento do webhook."""
    order_id = order_for_payment["id"]
    event_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"order_id": str(order_id)},
                "payment_status": "paid",
            }
        },
    }
    mocker.patch("stripe.Webhook.construct_event", return_value=event_payload)

    mocker.patch(
        "sqlalchemy.orm.Session.commit", side_effect=Exception("DB commit failed")
    )

    response = client.post(
        "/payments/webhook",
        json=event_payload,
        headers={"Stripe-Signature": "dummy_sig"},
    )

    assert response.status_code == 500
    assert (
        response.json()["detail"]
        == "Database processing failed. Webhook will be retried."
    )
