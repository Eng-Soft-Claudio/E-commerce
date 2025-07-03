"""
Suíte de Testes para o recurso de Categorias (Categories).

Testa todos os endpoints sob o prefixo '/categories', garantindo que:
- O acesso público para leitura de categorias funciona como esperado.
- As permissões para operações de escrita (criar, atualizar, deletar) estão
  corretamente aplicadas, permitindo apenas superusuários.
- O ciclo completo de CRUD (Create, Read, Update, Delete) de uma categoria
  pode ser executado por um superusuário.
- Casos de borda, como solicitar uma categoria inexistente, retornam os
  erros HTTP apropriados.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from fastapi.testclient import TestClient
from typing import Dict

# -------------------------------------------------------------------------- #
#                             TESTES DE ACESSO PÚBLICO                       #
# -------------------------------------------------------------------------- #


def test_read_categories_publicly_on_clean_db(client: TestClient):
    """Testa se GET /categories/ em um BD limpo retorna uma lista vazia."""
    response = client.get("/categories/")
    assert response.status_code == 200
    assert response.json() == []


def test_read_single_category_not_found(client: TestClient):
    """Testa GET /categories/{id} com um ID inexistente, esperando 404."""
    response = client.get("/categories/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Categoria não encontrada."


def test_create_category_unauthorized(client: TestClient):
    """Testa se POST /categories/ é bloqueado para clientes não autenticados."""
    category_data = {"title": "Proibido", "description": "Não será criado"}
    response = client.post("/categories/", json=category_data)
    assert response.status_code == 401


# -------------------------------------------------------------------------- #
#                   TESTES DE CONTROLE DE ACESSO (PERMISSÕES)                #
# -------------------------------------------------------------------------- #


def test_create_category_as_common_user_is_forbidden(
    client: TestClient, user_token_headers: Dict
):
    """Testa se um usuário comum não pode criar uma categoria (espera 403)."""
    category_data = {"title": "Falha", "description": "Criado por usuário comum"}
    response = client.post(
        "/categories/", headers=user_token_headers, json=category_data
    )
    assert response.status_code == 403, response.text
    assert "enough privileges" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                  TESTES DE CRUD COMPLETO (COMO SUPERUSER)                  #
# -------------------------------------------------------------------------- #


def test_superuser_crud_cycle(client: TestClient, superuser_token_headers: Dict):
    """
    Testa o ciclo de vida completo de uma categoria (CRUD) por um superuser.
    1. Criação
    2. Leitura
    3. Atualização
    4. Deleção
    5. Confirmação da Deleção
    """
    create_data = {"title": "Eletrônicos", "description": "Dispositivos"}
    create_response = client.post(
        "/categories/", headers=superuser_token_headers, json=create_data
    )
    assert create_response.status_code == 201
    category = create_response.json()
    category_id = category["id"]

    get_response = client.get(f"/categories/{category_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == create_data["title"]

    update_data = {"title": "Eletrônicos e Gadgets", "description": "Atualizado"}
    update_response = client.put(
        f"/categories/{category_id}", headers=superuser_token_headers, json=update_data
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == update_data["title"]

    delete_response = client.delete(
        f"/categories/{category_id}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 200

    confirm_get_response = client.get(f"/categories/{category_id}")
    assert confirm_get_response.status_code == 404


def test_superuser_update_nonexistent_category(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a atualização de uma categoria com ID inexistente (espera 404)."""
    response = client.put(
        "/categories/999",
        headers=superuser_token_headers,
        json={"title": "Fantasma"},
    )
    assert response.status_code == 404


def test_superuser_delete_nonexistent_category(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a deleção de uma categoria com ID inexistente (espera 404)."""
    response = client.delete("/categories/999", headers=superuser_token_headers)
    assert response.status_code == 404
