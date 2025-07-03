"""
Suíte de Testes para o recurso de Carrinho de Compras (Shopping Cart).

Testa todos os endpoints sob o prefixo '/cart', cobrindo:
- A verificação de permissão (ex: superusuários não podem ter carrinho).
- O fluxo de vida completo de um item no carrinho de um usuário comum.
- A validação de estoque ao adicionar ou atualizar itens no carrinho.
- Casos de borda como adicionar produtos inexistentes, solicitar mais
  produtos do que o disponível em estoque ou manipular um carrinho vazio.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import Dict

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from sqlalchemy.orm import Session
from src import models, crud
from src.auth import create_access_token
from src.schemas import UserCreate

# -------------------------------------------------------------------------- #
#                        FIXTURE AUXILIAR DE SETUP                           #
# -------------------------------------------------------------------------- #


@pytest.fixture
def product_for_cart_tests(client: TestClient, superuser_token_headers: Dict) -> Dict:
    """Fixture para criar uma categoria e um produto com estoque para testes."""
    cat_resp = client.post(
        "/categories/",
        headers=superuser_token_headers,
        json={"title": "Carrinho Categ"},
    )
    cat_resp.raise_for_status()
    prod_data = {
        "sku": "PROD-CART-001",
        "name": "Item Teste Carrinho",
        "price": 10.99,
        "category_id": cat_resp.json()["id"],
        "stock": 5,
        "weight_kg": 0.2,
        "height_cm": 5,
        "width_cm": 10,
        "length_cm": 15,
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    prod_resp.raise_for_status()
    return prod_resp.json()


# -------------------------------------------------------------------------- #
#                         TESTES DE CONTROLE DE ACESSO                       #
# -------------------------------------------------------------------------- #


def test_superuser_has_no_cart(client: TestClient, superuser_token_headers: Dict):
    """Testa se superusuários não podem acessar o endpoint do carrinho (espera 403)."""
    response = client.get("/cart/", headers=superuser_token_headers)
    assert response.status_code == 403, response.text
    assert "Superusuários não possuem carrinho de compras" in response.json()["detail"]


def test_superuser_cannot_add_or_update_cart(
    client: TestClient, superuser_token_headers: Dict, product_for_cart_tests: Dict
):
    """
    Testa se o superusuário é proibido de adicionar ou atualizar itens,
    cobrirá as linhas que faltavam nessas rotas.
    """
    product_id = product_for_cart_tests["id"]
    add_response = client.post(
        "/cart/items/",
        headers=superuser_token_headers,
        json={"product_id": 1, "quantity": 1},
    )
    assert add_response.status_code == 403

    update_response = client.put(
        f"/cart/items/{product_id}",
        headers=superuser_token_headers,
        json={"quantity": 1},
    )
    assert update_response.status_code == 403


def test_read_cart_when_cart_is_missing(client: TestClient, db_session, test_user):
    """Testa o caso raro de um usuário não ter um carrinho associado."""
    user_in_db = crud.get_user_by_email(db_session, test_user["email"])
    assert user_in_db is not None
    assert user_in_db.cart is not None

    user_token = create_access_token(data={"sub": user_in_db.email})
    headers = {"Authorization": f"Bearer {user_token}"}

    db_session.delete(user_in_db.cart)
    db_session.commit()

    response = client.get("/cart/", headers=headers)
    assert response.status_code == 200
    assert "id" in response.json()


# -------------------------------------------------------------------------- #
#               TESTES DO FLUXO DO CARRINHO COM VALIDAÇÃO DE ESTOQUE         #
# -------------------------------------------------------------------------- #


def test_add_item_to_cart_success(
    client: TestClient, user_token_headers: Dict, product_for_cart_tests: Dict
):
    """Testa adicionar com sucesso um item ao carrinho (dentro do limite de estoque)."""
    product_id = product_for_cart_tests["id"]

    response = client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 2},
    )
    assert response.status_code == 200, response.text

    response_2 = client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 3},
    )
    assert response_2.status_code == 200, response_2.text

    cart_resp = client.get("/cart/", headers=user_token_headers)
    assert cart_resp.json()["items"][0]["quantity"] == 5


def test_add_item_to_cart_insufficient_stock(
    client: TestClient, user_token_headers: Dict, product_for_cart_tests: Dict
):
    """Testa a falha ao tentar adicionar um item que excede o estoque disponível."""
    product_id = product_for_cart_tests["id"]

    response = client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 6},
    )
    assert response.status_code == 400, response.text
    assert "Estoque insuficiente" in response.json()["detail"]


def test_update_cart_item_quantity_success(
    client: TestClient, user_token_headers: Dict, product_for_cart_tests: Dict
):
    """Testa a atualização bem-sucedida da quantidade de um item no carrinho."""
    product_id = product_for_cart_tests["id"]
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 1},
    ).raise_for_status()

    update_response = client.put(
        f"/cart/items/{product_id}",
        headers=user_token_headers,
        json={"quantity": 4},
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["quantity"] == 4


def test_update_cart_item_insufficient_stock(
    client: TestClient, user_token_headers: Dict, product_for_cart_tests: Dict
):
    """Testa a falha ao atualizar a quantidade para um valor maior que o estoque."""
    product_id = product_for_cart_tests["id"]
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 1},
    ).raise_for_status()

    update_response = client.put(
        f"/cart/items/{product_id}",
        headers=user_token_headers,
        json={"quantity": 6},
    )
    assert update_response.status_code == 404, update_response.text
    assert (
        "Item não encontrado no carrinho ou estoque insuficiente"
        in update_response.json()["detail"]
    )


# -------------------------------------------------------------------------- #
#                             TESTES DE CASOS DE BORDA                       #
# -------------------------------------------------------------------------- #


def test_add_nonexistent_product_to_cart(client: TestClient, user_token_headers: Dict):
    """Testa adicionar um produto com ID inválido ao carrinho (espera 404)."""
    item_data = {"product_id": 9999, "quantity": 1}
    response = client.post("/cart/items/", headers=user_token_headers, json=item_data)
    assert response.status_code == 404
    assert "Produto não encontrado" in response.json()["detail"]


def test_update_item_not_in_cart(
    client: TestClient, user_token_headers: Dict, product_for_cart_tests: Dict
):
    """
    Testa a falha ao tentar atualizar a quantidade de um produto
    que não está no carrinho.
    """
    product_id = product_for_cart_tests["id"]
    response = client.put(
        f"/cart/items/{product_id}",
        headers=user_token_headers,
        json={"quantity": 2},
    )
    assert response.status_code == 404
    assert (
        "Item não encontrado no carrinho ou estoque insuficiente"
        in response.json()["detail"]
    )


def test_update_cart_item_to_zero_removes_item(
    client: TestClient, user_token_headers: Dict, product_for_cart_tests: Dict
):
    """
    Testa se tentar atualizar um item com quantidade 0 o remove do carrinho.
    Este teste cobre as linhas 232-233 do CRUD.
    """
    product_id = product_for_cart_tests["id"]
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 2},
    ).raise_for_status()

    update_response: Response = client.put(
        f"/cart/items/{product_id}", headers=user_token_headers, json={"quantity": 0}
    )
    assert update_response.status_code == 204

    cart_response = client.get("/cart/", headers=user_token_headers)
    assert not cart_response.json()["items"]


# -------------------------------------------------------------------------- #
#                        TESTES DE CASOS DE BORDA E FALHAS                   #
# -------------------------------------------------------------------------- #


def test_superuser_cannot_delete_from_cart(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa se superusuário é proibido de usar a rota DELETE do carrinho."""
    response = client.delete("/cart/items/1", headers=superuser_token_headers)
    assert response.status_code == 403, response.text


def test_manipulate_cart_when_cart_is_missing(
    client: TestClient,
    db_session: Session,
    test_user_payload: Dict,
    superuser_token_headers: Dict,
):
    """
    Testa que todas as rotas de manipulação de itens falham corretamente se
    um usuário, por algum motivo, não tiver um carrinho associado.
    """
    cat_resp = client.post(
        "/categories/", headers=superuser_token_headers, json={"title": "Cat"}
    )
    cat_resp.raise_for_status()
    prod_data = {
        "sku": "SKU-NOCART",
        "name": "Prod",
        "price": 10,
        "category_id": cat_resp.json()["id"],
        "weight_kg": 0.1,
        "height_cm": 1,
        "width_cm": 1,
        "length_cm": 1,
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    prod_resp.raise_for_status()
    product_id = prod_resp.json()["id"]

    user = crud.create_user(db_session, user=UserCreate(**test_user_payload))
    cart_to_delete = db_session.query(models.Cart).filter_by(user_id=user.id).first()
    assert cart_to_delete is not None
    db_session.delete(cart_to_delete)
    db_session.commit()

    user_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {user_token}"}

    add_response = client.post(
        "/cart/items/", headers=headers, json={"product_id": product_id, "quantity": 1}
    )
    assert add_response.status_code == 404
    assert "Carrinho do usuário não encontrado" in add_response.json()["detail"]

    update_response = client.put(
        f"/cart/items/{product_id}", headers=headers, json={"quantity": 2}
    )
    assert update_response.status_code == 404
    assert "Carrinho do usuário não encontrado" in update_response.json()["detail"]

    delete_response = client.delete(f"/cart/items/{product_id}", headers=headers)
    assert delete_response.status_code == 404
    assert "Carrinho do usuário não encontrado" in delete_response.json()["detail"]


def test_remove_nonexistent_product_from_cart(
    client: TestClient, user_token_headers: Dict
):
    """
    Testa a falha ao tentar remover um produto que não está no carrinho.
    Cobre a linha 154.
    """
    response = client.delete("/cart/items/9999", headers=user_token_headers)
    assert response.status_code == 404
    assert "Produto não encontrado no carrinho" in response.json()["detail"]
