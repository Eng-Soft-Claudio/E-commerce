"""
Suíte de Testes para o recurso de Pedidos (Orders).

Testa todos os endpoints sob o prefixo '/orders', cobrindo o fluxo de vida
completo de um pedido. Foco principal em validar a lógica de negócio crítica:
- A criação de um pedido só é possível com um carrinho não vazio.
- O débito do estoque do produto é feito corretamente após o pedido ser criado.
- O carrinho do usuário é esvaziado após a criação do pedido.
- A criação do pedido falha se o estoque de um item for insuficiente no
  momento da finalização (checagem de concorrência).
- Validações de permissão, garantindo que usuários comuns não possam ver
  pedidos de outros usuários.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models, crud
from src.auth import create_access_token
from src.schemas import UserCreate

# -------------------------------------------------------------------------- #
#                         FUNÇÃO AUXILIAR DE SETUP                           #
# -------------------------------------------------------------------------- #


def create_product_for_order(
    client: TestClient, headers: Dict[str, str], sku: str
) -> Dict[str, Any]:
    """Cria uma categoria e um produto com estoque para ser usado nos testes."""
    cat_resp = client.post(
        "/categories/", headers=headers, json={"title": f"Cat-{sku}"}
    )
    cat_resp.raise_for_status()
    prod_data = {
        "sku": sku,
        "name": f"Item {sku}",
        "price": 25.50,
        "category_id": cat_resp.json()["id"],
        "stock": 10,
        "weight_kg": 0.3,
        "height_cm": 4,
        "width_cm": 12,
        "length_cm": 18,
    }
    prod_resp = client.post("/products/", headers=headers, json=prod_data)
    prod_resp.raise_for_status()
    return prod_resp.json()


# -------------------------------------------------------------------------- #
#                         TESTES DE CONTROLE DE ACESSO                       #
# -------------------------------------------------------------------------- #


def test_create_order_from_empty_cart_fails(
    client: TestClient, user_token_headers: Dict
):
    """Testa a falha de criação de um pedido com um carrinho vazio (espera 400)."""
    response = client.post("/orders/", headers=user_token_headers)
    assert response.status_code == 400, response.text
    assert "Carrinho vazio" in response.json()["detail"]


def test_superuser_cannot_create_order(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa que superusuários não podem criar pedidos (espera 403)."""
    response = client.post("/orders/", headers=superuser_token_headers)
    assert response.status_code == 403, response.text


def test_create_order_unauthorized(client: TestClient):
    """Testa que clientes não autenticados não podem criar pedidos (espera 401)."""
    response = client.post("/orders/")
    assert response.status_code == 401, response.text


# -------------------------------------------------------------------------- #
#            TESTES DO FLUXO DE PEDIDO E LÓGICA DE ESTOQUE                   #
# -------------------------------------------------------------------------- #


def test_order_creation_success_and_stock_deduction(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
    db_session: Session,
):
    """
    Testa o fluxo de ponta-a-ponta: popular carrinho -> criar pedido ->
    verificar débito do estoque -> verificar carrinho vazio.
    """
    product = create_product_for_order(client, superuser_token_headers, "PROD-ORD-001")
    product_id = product["id"]
    initial_stock = product["stock"]
    quantity_to_buy = 2

    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": quantity_to_buy},
    ).raise_for_status()

    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201, order_response.text

    product_in_db = db_session.get(models.Product, product_id)
    assert product_in_db is not None, "Produto deveria ser encontrado no DB"
    assert product_in_db.stock == initial_stock - quantity_to_buy

    cart_response = client.get("/cart/", headers=user_token_headers)
    assert not cart_response.json()["items"]


def test_order_creation_fails_if_stock_is_insufficient_at_checkout(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
    db_session: Session,
):
    """
    Testa o cenário de concorrência: um item está no carrinho, mas seu
    estoque é reduzido por outra via antes da finalização da compra.
    """
    product = create_product_for_order(client, superuser_token_headers, "PROD-ORD-002")
    product_id = product["id"]

    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 5},
    ).raise_for_status()

    product_in_db = db_session.get(models.Product, product_id)
    assert product_in_db is not None, "Produto deveria ser encontrado no DB"
    product_in_db.stock = 3
    db_session.commit()

    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 400, order_response.text
    assert "Estoque insuficiente" in order_response.json()["detail"]


def test_user_cannot_see_another_users_order(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
    db_session: Session,
):
    """Testa se um usuário comum não pode visualizar o pedido de outro usuário."""
    user_b_payload = {
        "email": "user.b@test.com",
        "password": "passwordB",
        "full_name": "User B",
        "cpf": "93963227095",
        "phone": "(33)77777-7777",
        "address_street": "Rua B",
        "address_number": "3",
        "address_zip": "67890-000",
        "address_city": "Cidade B",
        "address_state": "AC",
    }
    crud.create_user(db_session, user=UserCreate(**user_b_payload))
    user_b_token = create_access_token(data={"sub": user_b_payload["email"]})
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

    product = create_product_for_order(client, superuser_token_headers, "PROD-ORD-B")
    client.post(
        "/cart/items/",
        headers=user_b_headers,
        json={"product_id": product["id"], "quantity": 1},
    ).raise_for_status()
    order_b_response = client.post("/orders/", headers=user_b_headers)
    order_b_id = order_b_response.json()["id"]

    response = client.get(f"/orders/{order_b_id}", headers=user_token_headers)
    assert response.status_code == 403, response.text
    assert "Não autorizado a visualizar este pedido" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                    TESTES DE CASOS DE BORDA E FALHAS                       #
# -------------------------------------------------------------------------- #


def test_order_creation_handles_unexpected_db_error(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
    mocker,
):
    """
    Testa se um erro inesperado do banco de dados durante a criação do pedido
    é tratado corretamente, retornando um status 500.
    """
    product = create_product_for_order(client, superuser_token_headers, "PROD-ERR-01")
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product["id"], "quantity": 1},
    ).raise_for_status()

    mocker.patch(
        "sqlalchemy.orm.Session.commit",
        side_effect=Exception("Simulated unexpected database error"),
    )

    response = client.post("/orders/", headers=user_token_headers)

    assert response.status_code == 500, response.text
    assert "Ocorreu um erro inesperado" in response.json()["detail"]


def test_read_single_nonexistent_order(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """Testa a busca por um pedido com um ID que não existe (espera 404)."""
    response = client.get("/orders/9999", headers=user_token_headers)
    assert response.status_code == 404


# -------------------------------------------------------------------------- #
#                    TESTES DE CASOS DE BORDA E FALHAS                       #
# -------------------------------------------------------------------------- #


def test_order_creation_fails_if_product_is_deleted(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
    db_session: Session,
):
    """
    Testa a falha na criação de um pedido se um produto no carrinho
    foi deletado antes da finalização.
    """
    product = create_product_for_order(client, superuser_token_headers, "PROD-DEL-01")
    product_id = product["id"]

    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 1},
    ).raise_for_status()

    db_product = db_session.get(models.Product, product_id)
    assert db_product is not None
    db_session.delete(db_product)
    db_session.commit()

    response = client.post("/orders/", headers=user_token_headers)
    assert response.status_code == 400, response.text
    assert "não existe mais" in response.json()["detail"]


def test_read_my_orders_returns_list(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """
    Testa se a rota para ler os próprios pedidos retorna uma lista, cobrindo a
    função CRUD subjacente.
    """
    response = client.get("/orders/", headers=user_token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
