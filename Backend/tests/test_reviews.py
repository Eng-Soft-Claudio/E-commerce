"""
Suíte de Testes para o recurso de Avaliações de Produtos (Reviews).
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

import pytest
from typing import Dict, Any

from fastapi.testclient import TestClient

# -------------------------------------------------------------------------- #
#                                 FIXTURES                                   #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def product_for_review(
    client: TestClient, superuser_token_headers: Dict
) -> Dict[str, Any]:
    """Cria uma categoria e um produto para serem usados nos testes de avaliação."""
    cat_resp = client.post(
        "/categories/",
        headers=superuser_token_headers,
        json={"title": "Categoria Review"},
    )
    cat_resp.raise_for_status()

    prod_data = {
        "sku": "PROD-REV-01",
        "name": "Produto para Avaliar",
        "price": 50.0,
        "category_id": cat_resp.json()["id"],
        "stock": 100,
        "weight_kg": 0.1,
        "height_cm": 2,
        "width_cm": 10,
        "length_cm": 15,
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    prod_resp.raise_for_status()
    return prod_resp.json()


# -------------------------------------------------------------------------- #
#                 TESTES DE CRIAÇÃO E LEITURA DE AVALIAÇÕES                  #
# -------------------------------------------------------------------------- #


def test_create_and_read_review_cycle(
    client: TestClient,
    user_token_headers: Dict,
    product_for_review: Dict,
    test_user: Dict,
):
    """
    Testa o fluxo completo: criar uma avaliação, lê-la na lista de avaliações
    do produto e também na rota do próprio produto.
    """
    product_id = product_for_review["id"]
    review_data = {"rating": 5, "comment": "Produto excelente!"}

    create_resp = client.post(
        f"/products/{product_id}/reviews", headers=user_token_headers, json=review_data
    )
    assert create_resp.status_code == 201, create_resp.text
    review_json = create_resp.json()
    assert review_json["rating"] == 5
    assert review_json["comment"] == "Produto excelente!"
    assert review_json["author"]["id"] == test_user["id"]
    assert review_json["author"]["full_name"] == test_user["full_name"]

    list_resp = client.get(f"/products/{product_id}/reviews")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == review_json["id"]

    product_resp = client.get(f"/products/{product_id}")
    assert product_resp.status_code == 200
    assert len(product_resp.json()["reviews"]) == 1
    assert product_resp.json()["reviews"][0]["comment"] == "Produto excelente!"


def test_get_reviews_for_nonexistent_product(client: TestClient):
    """Testa a falha ao tentar listar avaliações de um produto inexistente."""
    response = client.get("/products/99999/reviews")
    assert response.status_code == 404
    assert "Produto não encontrado" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                        TESTES DE CONTROLE DE ACESSO                        #
# -------------------------------------------------------------------------- #


def test_create_review_unauthorized(client: TestClient, product_for_review: Dict):
    """Testa se um usuário não autenticado não pode criar uma avaliação."""
    product_id = product_for_review["id"]
    review_data = {"rating": 4}
    response = client.post(f"/products/{product_id}/reviews", json=review_data)
    assert response.status_code == 401


def test_create_review_for_nonexistent_product(
    client: TestClient, user_token_headers: Dict
):
    """Testa a falha ao tentar avaliar um produto que não existe."""
    review_data = {"rating": 5}
    response = client.post(
        "/products/99999/reviews", headers=user_token_headers, json=review_data
    )
    assert response.status_code == 404


def test_create_duplicate_review_fails(
    client: TestClient, user_token_headers: Dict, product_for_review: Dict
):
    """Testa a falha ao tentar criar uma segunda avaliação para o mesmo produto."""
    product_id = product_for_review["id"]
    review_data = {"rating": 5}
    client.post(
        f"/products/{product_id}/reviews", headers=user_token_headers, json=review_data
    ).raise_for_status()

    response = client.post(
        f"/products/{product_id}/reviews", headers=user_token_headers, json=review_data
    )
    assert response.status_code == 409
    assert "Este usuário já avaliou o produto" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                   TESTES DE GERENCIAMENTO (DELETE)                         #
# -------------------------------------------------------------------------- #


def test_admin_can_delete_review(
    client: TestClient,
    user_token_headers: Dict,
    superuser_token_headers: Dict,
    product_for_review: Dict,
):
    """Testa se um superusuário pode deletar qualquer avaliação."""
    product_id = product_for_review["id"]
    review_data = {"rating": 1, "comment": "Para ser deletado"}
    create_resp = client.post(
        f"/products/{product_id}/reviews", headers=user_token_headers, json=review_data
    )
    review_id = create_resp.json()["id"]

    delete_resp = client.delete(
        f"/reviews/{review_id}", headers=superuser_token_headers
    )
    assert delete_resp.status_code == 204

    # Verificar que foi deletado
    get_resp = client.get(f"/products/{product_id}/reviews")
    assert len(get_resp.json()) == 0


def test_user_cannot_delete_review(
    client: TestClient, user_token_headers: Dict, product_for_review: Dict
):
    """Testa se um usuário comum não pode deletar uma avaliação."""
    product_id = product_for_review["id"]
    review_data = {"rating": 1}
    create_resp = client.post(
        f"/products/{product_id}/reviews", headers=user_token_headers, json=review_data
    )
    review_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/reviews/{review_id}", headers=user_token_headers)
    assert delete_resp.status_code == 403


def test_admin_delete_nonexistent_review(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao deletar uma avaliação com ID inexistente."""
    response = client.delete("/reviews/99999", headers=superuser_token_headers)
    assert response.status_code == 404
    assert "Avaliação não encontrada" in response.json()["detail"]