"""
Suíte de Testes para o recurso de Cupons de Desconto.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

import pytest
from typing import Dict, Any

from fastapi.testclient import TestClient

# -------------------------------------------------------------------------- #
#                         TESTES DE CRUD DE CUPONS (ADMIN)                   #
# -------------------------------------------------------------------------- #


def test_admin_coupon_crud_cycle(client: TestClient, superuser_token_headers: Dict):
    """Testa o ciclo de vida completo (CRUD) de um cupom por um superusuário."""
    create_data = {"code": "NATAL25", "discount_percent": 25.0, "is_active": True}
    create_resp = client.post(
        "/coupons/", headers=superuser_token_headers, json=create_data
    )
    assert create_resp.status_code == 201, create_resp.text
    coupon_json = create_resp.json()
    coupon_id = coupon_json["id"]
    assert coupon_json["code"] == "NATAL25"

    list_resp = client.get("/coupons/", headers=superuser_token_headers)
    assert list_resp.status_code == 200
    assert any(c["id"] == coupon_id for c in list_resp.json())

    fail_create_resp = client.post(
        "/coupons/", headers=superuser_token_headers, json=create_data
    )
    assert fail_create_resp.status_code == 400

    update_data = {"is_active": False}
    update_resp = client.put(
        f"/coupons/{coupon_id}", headers=superuser_token_headers, json=update_data
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_active"] is False

    delete_resp = client.delete(
        f"/coupons/{coupon_id}", headers=superuser_token_headers
    )
    assert delete_resp.status_code == 204

    confirm_delete_resp = client.put(
        f"/coupons/{coupon_id}", headers=superuser_token_headers, json=update_data
    )
    assert confirm_delete_resp.status_code == 404

    fail_delete_resp = client.delete("/coupons/999", headers=superuser_token_headers)
    assert fail_delete_resp.status_code == 404


def test_common_user_cannot_manage_coupons(
    client: TestClient, user_token_headers: Dict
):
    """Testa que um usuário comum não tem acesso aos endpoints de CRUD de cupons."""
    resp_get = client.get("/coupons/", headers=user_token_headers)
    assert resp_get.status_code == 403

    resp_post = client.post(
        "/coupons/",
        headers=user_token_headers,
        json={"code": "FAIL", "discount_percent": 10},
    )
    assert resp_post.status_code == 403


# -------------------------------------------------------------------------- #
#                   TESTES DE APLICAÇÃO DE CUPOM NO CARRINHO                 #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def product_for_coupon(
    client: TestClient, superuser_token_headers: Dict
) -> Dict[str, Any]:
    """Cria um produto para os testes de aplicação de cupom."""
    cat_resp = client.post(
        "/categories/",
        headers=superuser_token_headers,
        json={"title": "Categoria Cupom"},
    )
    cat_resp.raise_for_status()

    prod_data = {
        "sku": "PROD-CUP-01",
        "name": "Produto para Cupom",
        "price": 100.0,
        "category_id": cat_resp.json()["id"],
        "stock": 10,
        "weight_kg": 0.5,
        "height_cm": 5,
        "width_cm": 20,
        "length_cm": 20,
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    prod_resp.raise_for_status()
    return prod_resp.json()


def test_apply_and_remove_valid_coupon(
    client: TestClient,
    superuser_token_headers: Dict,
    user_token_headers: Dict,
    product_for_coupon: Dict,
):
    """Testa aplicar, ver o desconto e remover um cupom válido do carrinho."""
    client.post(
        "/coupons/",
        headers=superuser_token_headers,
        json={"code": "DEZCONTO", "discount_percent": 10.0},
    ).raise_for_status()
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_for_coupon["id"], "quantity": 1},
    ).raise_for_status()

    apply_resp = client.post(
        "/cart/apply-coupon", headers=user_token_headers, json={"code": "DEZCONTO"}
    )
    assert apply_resp.status_code == 200, apply_resp.text
    cart_json = apply_resp.json()
    assert cart_json["subtotal"] == 100.0
    assert cart_json["discount_amount"] == 10.0
    assert cart_json["final_price"] == 90.0
    assert cart_json["coupon"]["code"] == "DEZCONTO"

    remove_resp = client.delete("/cart/apply-coupon", headers=user_token_headers)
    assert remove_resp.status_code == 200, remove_resp.text
    cart_json_after_remove = remove_resp.json()
    assert cart_json_after_remove["discount_amount"] == 0.0
    assert cart_json_after_remove["final_price"] == 100.0
    assert cart_json_after_remove["coupon"] is None


def test_apply_invalid_coupon(client: TestClient, user_token_headers: Dict):
    """Testa a falha ao tentar aplicar um cupom que não existe."""
    response = client.post(
        "/cart/apply-coupon", headers=user_token_headers, json={"code": "CUPOM-FALSO"}
    )
    assert response.status_code == 404
    assert "inválido ou expirado" in response.json()["detail"]


def test_order_creation_with_coupon(
    client: TestClient,
    superuser_token_headers: Dict,
    user_token_headers: Dict,
    product_for_coupon: Dict,
):
    """Testa a criação de um pedido a partir de um carrinho com cupom, verificando se o desconto é persistido."""
    client.post(
        "/coupons/",
        headers=superuser_token_headers,
        json={"code": "PEDIDO20", "discount_percent": 20.0},
    ).raise_for_status()
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_for_coupon["id"], "quantity": 2},
    ).raise_for_status()
    client.post(
        "/cart/apply-coupon", headers=user_token_headers, json={"code": "PEDIDO20"}
    ).raise_for_status()

    order_resp = client.post("/orders/", headers=user_token_headers)
    assert order_resp.status_code == 201, order_resp.text
    order_json = order_resp.json()
    assert order_json["total_price"] == 160.0
    assert order_json["discount_amount"] == 40.0
    assert order_json["coupon_code_used"] == "PEDIDO20"

    cart_resp = client.get("/cart/", headers=user_token_headers)
    assert not cart_resp.json()["items"]
    assert cart_resp.json()["coupon"] is None
