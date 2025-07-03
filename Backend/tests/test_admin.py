"""
Suíte de Testes para Endpoints de Administração.

Testa todas as rotas protegidas sob os prefixos '/admin' ou que requerem
privilégios de superusuário. Garante que:
1.  As permissões de acesso funcionam, bloqueando usuários comuns.
2.  Superusuários podem listar clientes e pedidos.
3.  A atualização de status de pedidos funciona como esperado.
4.  O painel de estatísticas (`/admin/stats`) retorna dados agregados
    corretamente.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

import pytest
from typing import Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Order, User  # noqa: F401

# -------------------------------------------------------------------------- #
#                        FIXTURE AUXILIAR DE SETUP                           #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def order_for_admin_tests(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
) -> Dict[str, Any]:
    """
    Fixture que cria um cenário completo para testes de administração:
    Cria uma categoria, um produto com estoque, um usuário comum adiciona o
    produto ao carrinho e, finalmente, cria um pedido.
    """
    cat_resp = client.post(
        "/categories/",
        headers=superuser_token_headers,
        json={"title": "Admin Test Categ"},
    )
    cat_resp.raise_for_status()
    category_id = cat_resp.json()["id"]

    prod_data = {
        "sku": "ADM-TEST-001",
        "name": "Produto para Teste Admin",
        "price": 99.99,
        "category_id": category_id,
        "stock": 10,
        "weight_kg": 1.0,
        "height_cm": 10,
        "width_cm": 10,
        "length_cm": 10,
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    prod_resp.raise_for_status()
    product_id = prod_resp.json()["id"]

    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 1},
    ).raise_for_status()

    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    return order_response.json()


# -------------------------------------------------------------------------- #
#                  TESTES PARA O ENDPOINT GET /admin/users                   #
# -------------------------------------------------------------------------- #


def test_superuser_can_list_users(
    client: TestClient, superuser_token_headers: Dict, test_user: Dict
):
    """Testa se um superusuário pode listar todos os usuários clientes."""
    response = client.get("/admin/users/", headers=superuser_token_headers)
    assert response.status_code == 200, response.text
    users_data = response.json()
    assert isinstance(users_data, list)
    assert any(user["email"] == test_user["email"] for user in users_data)


def test_common_user_cannot_list_users(client: TestClient, user_token_headers: Dict):
    """Testa se um usuário comum é proibido de acessar a lista de usuários."""
    response = client.get("/admin/users/", headers=user_token_headers)
    assert response.status_code == 403


# -------------------------------------------------------------------------- #
#              TESTES PARA ENDPOINTS DE GERENCIAMENTO DE PEDIDOS             #
# -------------------------------------------------------------------------- #


def test_superuser_cannot_read_own_orders(
    client: TestClient, superuser_token_headers: Dict
):
    """
    Testa que um superusuário não pode acessar a rota /orders, pois não possui
    histórico de pedidos. Cobre a linha 104.
    """
    response = client.get("/orders/", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_update_nonexistent_order_status(
    client: TestClient, superuser_token_headers: Dict
):
    """
    Testa a falha ao tentar atualizar um pedido com ID inexistente. Cobre a linha 136.
    """
    response = client.put(
        "/orders/9999/status", headers=superuser_token_headers, json={"status": "paid"}
    )
    assert response.status_code == 404, response.text
    assert "Pedido não encontrado" in response.json()["detail"]


def test_update_order_with_invalid_status(
    client: TestClient, superuser_token_headers: Dict, order_for_admin_tests: Dict
):
    """
    Testa a falha ao usar um valor de status inválido. Cobre a linha 140.
    """
    order_id = order_for_admin_tests["id"]
    response = client.put(
        f"/orders/{order_id}/status",
        headers=superuser_token_headers,
        json={"status": "status_inventado"},
    )
    assert response.status_code == 400, response.text
    assert "é inválido" in response.json()["detail"]


def test_update_order_status_fails_on_reload(
    client: TestClient,
    superuser_token_headers: Dict,
    order_for_admin_tests: Dict,
    mocker,
):
    """
    Testa a falha de recarregamento do pedido após o update. Cobre a linha 158.
    """
    order_id = order_for_admin_tests["id"]

    mock_query = mocker.patch("sqlalchemy.orm.Session.query")
    mock_query.return_value.options.return_value.filter.return_value.first.return_value = None

    response = client.put(
        f"/orders/{order_id}/status",
        headers=superuser_token_headers,
        json={"status": "paid"},
    )

    assert response.status_code == 500
    assert "Falha ao recarregar" in response.json()["detail"]


def test_superuser_can_list_all_orders(
    client: TestClient,
    superuser_token_headers: Dict,
    order_for_admin_tests: Dict,
):
    """Testa se um superusuário pode listar todos os pedidos no sistema."""
    response = client.get("/orders/admin/all", headers=superuser_token_headers)
    assert response.status_code == 200, response.text
    assert any(order["id"] == order_for_admin_tests["id"] for order in response.json())


def test_superuser_can_update_order_status(
    client: TestClient,
    superuser_token_headers: Dict,
    order_for_admin_tests: Dict,
    db_session: Session,
):
    """Testa a atualização bem-sucedida do status de um pedido por um superusuário."""
    order_id = order_for_admin_tests["id"]
    response = client.put(
        f"/orders/{order_id}/status",
        headers=superuser_token_headers,
        json={"status": "shipped"},
    )
    assert response.status_code == 200, response.text

    db_session.expire_all()
    order_after = db_session.get(Order, order_id)
    assert order_after is not None
    assert order_after.status == "shipped"


def test_superuser_can_read_any_single_order(
    client: TestClient, superuser_token_headers: Dict, order_for_admin_tests: Dict
):
    """
    Testa se um superusuário pode acessar diretamente o pedido de qualquer
    cliente através do endpoint GET /orders/{order_id}.
    """
    order_id = order_for_admin_tests["id"]

    response = client.get(f"/orders/{order_id}", headers=superuser_token_headers)

    assert response.status_code == 200, response.text
    assert response.json()["id"] == order_id


# -------------------------------------------------------------------------- #
#                 TESTES PARA O ENDPOINT GET /admin/stats                    #
# -------------------------------------------------------------------------- #


def test_get_dashboard_stats_with_data(
    client: TestClient,
    superuser_token_headers: Dict,
    order_for_admin_tests: Dict,
    db_session: Session,
):
    """Testa se as estatísticas do painel refletem corretamente os dados existentes."""
    response = client.get("/admin/stats/", headers=superuser_token_headers)
    data = response.json()
    assert data["total_orders"] == 1
    assert data["total_users"] >= 1
    assert data["total_sales"] == 0

    order_id = order_for_admin_tests["id"]
    order = db_session.get(Order, order_id)
    assert order is not None
    order.status = "paid"
    db_session.commit()

    response_after = client.get("/admin/stats/", headers=superuser_token_headers)
    assert response_after.json()["total_sales"] == 99.99
