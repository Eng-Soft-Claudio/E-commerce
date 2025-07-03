"""
Suíte de Testes para o recurso de Produtos (Products).

Testa todos os endpoints sob o prefixo '/products', cobrindo:
- Acesso público a endpoints de leitura.
- Controle de acesso baseado em permissões para operações de escrita.
- A lógica de negócio de associar um produto a uma categoria.
- Validação de SKU único na criação e atualização.
- Gerenciamento de estoque através dos endpoints de admin.
- Casos de borda como IDs não encontrados e dados inválidos.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import Dict

from fastapi.testclient import TestClient

# -------------------------------------------------------------------------- #
#                        FUNÇÃO AUXILIAR DE SETUP                            #
# -------------------------------------------------------------------------- #


def create_category_and_get_id(client: TestClient, headers: Dict, title: str) -> int:
    """Função auxiliar para criar uma categoria de teste e retornar seu ID."""
    category_data = {"title": title, "description": f"Categoria {title}"}
    response = client.post("/categories/", headers=headers, json=category_data)
    assert response.status_code == 201, response.text
    return response.json()["id"]


# -------------------------------------------------------------------------- #
#                       TESTES DE ACESSO PÚBLICO                             #
# -------------------------------------------------------------------------- #


def test_read_products_publicly(client: TestClient):
    """Testa se GET /products/ é público e retorna uma lista vazia em um BD limpo."""
    response = client.get("/products/")
    assert response.status_code == 200
    assert response.json() == []


def test_read_single_product_not_found(client: TestClient):
    """Testa a solicitação de um produto com um ID que não existe."""
    response = client.get("/products/9999")
    assert response.status_code == 404
    assert "Produto não encontrado" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#         TESTES DE CRUD COMPLETO E VALIDAÇÃO (COMO SUPERUSER)               #
# -------------------------------------------------------------------------- #


def test_superuser_product_crud_cycle(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa o ciclo de vida completo (CRUD) de um produto por um superuser."""
    category_id = create_category_and_get_id(
        client, superuser_token_headers, "Eletronicos"
    )

    product_data = {
        "name": "Laptop Pro",
        "sku": "LP12345",
        "price": 5000.0,
        "category_id": category_id,
        "stock": 10,
        "description": "Um laptop poderoso para profissionais.",
        "weight_kg": 1.8,
        "height_cm": 1.5,
        "width_cm": 35.0,
        "length_cm": 25.0,
    }
    create_response = client.post(
        "/products/", headers=superuser_token_headers, json=product_data
    )
    assert create_response.status_code == 201, create_response.text
    product = create_response.json()
    product_id = product["id"]

    assert product["name"] == product_data["name"]
    assert product["sku"] == product_data["sku"]
    assert product["stock"] == product_data["stock"]

    read_response = client.get(f"/products/{product_id}")
    assert read_response.status_code == 200
    assert read_response.json()["name"] == product_data["name"]

    update_data = {
        "name": "Laptop Ultra",
        "price": 5500.0,
        "stock": 5,
        "weight_kg": 1.7,
    }
    update_response = client.put(
        f"/products/{product_id}", headers=superuser_token_headers, json=update_data
    )
    assert update_response.status_code == 200, update_response.text
    updated_product = update_response.json()
    assert updated_product["name"] == update_data["name"]
    assert updated_product["price"] == update_data["price"]
    assert updated_product["stock"] == update_data["stock"]
    assert updated_product["weight_kg"] == 1.7

    delete_response = client.delete(
        f"/products/{product_id}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 200

    confirm_response = client.get(f"/products/{product_id}")
    assert confirm_response.status_code == 404


# -------------------------------------------------------------------------- #
#                 TESTES DE BUSCA E FILTRAGEM DE PRODUTOS                    #
# -------------------------------------------------------------------------- #


def test_search_and_filter_products_functionality(
    client: TestClient, superuser_token_headers: Dict
):
    """
    Testa a funcionalidade de busca e filtro de produtos de forma abrangente.
    Cria produtos em diferentes categorias com nomes e descrições distintos
    para validar os vários cenários de busca.
    """
    cat_a_id = create_category_and_get_id(
        client, superuser_token_headers, title="Roupas"
    )
    cat_b_id = create_category_and_get_id(
        client, superuser_token_headers, title="Calçados"
    )

    base_logistics = {"weight_kg": 0.3, "height_cm": 5, "width_cm": 20, "length_cm": 30}

    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={
            "name": "Camisa de Algodão",
            "sku": "CA-001",
            "price": 80,
            "category_id": cat_a_id,
            "description": "Tecido macio e confortável.",
            **base_logistics,
        },
    ).raise_for_status()
    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={
            "name": "Calça Jeans",
            "sku": "CJ-002",
            "price": 150,
            "category_id": cat_a_id,
            "description": "Jeans de alta durabilidade.",
            **base_logistics,
            "weight_kg": 0.7,
        },
    ).raise_for_status()
    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={
            "name": "Tênis de Corrida",
            "sku": "TC-003",
            "price": 350,
            "category_id": cat_b_id,
            "description": "Ideal para atletas de jeans.",
            **base_logistics,
            "weight_kg": 0.9,
            "height_cm": 12,
            "width_cm": 15,
            "length_cm": 35,
        },
    ).raise_for_status()

    response = client.get("/products/?q=camisa de algodão")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == "CA-001"

    response = client.get("/products/?q=Calça")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == "CJ-002"

    response = client.get("/products/?q=atletas")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == "TC-003"

    response = client.get("/products/?q=jeans")
    assert response.status_code == 200
    assert len(response.json()) == 2
    skus_found = {p["sku"] for p in response.json()}
    assert skus_found == {"CJ-002", "TC-003"}

    response = client.get(f"/products/?q=jeans&category_id={cat_a_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == "CJ-002"

    response = client.get("/products/?q=produto-fantasma-xyz")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_read_products_filtered_by_category(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa se a listagem de produtos com o filtro de categoria funciona."""
    cat_a_id = create_category_and_get_id(
        client, superuser_token_headers, title="Cat A"
    )
    cat_b_id = create_category_and_get_id(
        client, superuser_token_headers, title="Cat B"
    )

    base_logistics = {"weight_kg": 0.1, "height_cm": 1, "width_cm": 10, "length_cm": 15}

    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={
            "name": "Produto A",
            "sku": "PROD-A",
            "price": 10,
            "category_id": cat_a_id,
            **base_logistics,
        },
    ).raise_for_status()

    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={
            "name": "Produto B",
            "sku": "PROD-B",
            "price": 20,
            "category_id": cat_b_id,
            **base_logistics,
        },
    ).raise_for_status()

    response = client.get(f"/products/?category_id={cat_a_id}")
    assert response.status_code == 200

    products = response.json()
    assert len(products) == 1
    assert products[0]["name"] == "Produto A"
    assert products[0]["category"]["id"] == cat_a_id


# -------------------------------------------------------------------------- #
#                        TESTES DE CASOS DE BORDA                            #
# -------------------------------------------------------------------------- #


def test_create_product_with_duplicate_sku(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao criar um produto com um SKU que já existe."""
    category_id = create_category_and_get_id(client, superuser_token_headers, "Livros")
    product_data = {
        "name": "Livro de Teste",
        "sku": "LIVRO-SKU-UNICO",
        "price": 29.99,
        "category_id": category_id,
        "weight_kg": 0.4,
        "height_cm": 2,
        "width_cm": 15,
        "length_cm": 22,
    }
    client.post(
        "/products/", headers=superuser_token_headers, json=product_data
    ).raise_for_status()

    product_data_2 = {**product_data, "name": "Outro Livro"}
    response = client.post(
        "/products/", headers=superuser_token_headers, json=product_data_2
    )
    assert response.status_code == 400
    assert "SKU já cadastrado" in response.json()["detail"]


def test_update_product_with_duplicate_sku(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao atualizar um produto para um SKU que já pertence a outro."""
    category_id = create_category_and_get_id(
        client, superuser_token_headers, "Ferramentas"
    )
    base_logistics = {
        "weight_kg": 1.0,
        "height_cm": 10,
        "width_cm": 10,
        "length_cm": 40,
    }
    prod1_data = {
        "name": "Martelo",
        "sku": "FER-001",
        "price": 50,
        "category_id": category_id,
        **base_logistics,
    }
    client.post(
        "/products/", headers=superuser_token_headers, json=prod1_data
    ).raise_for_status()
    prod2_data = {
        "name": "Chave de Fenda",
        "sku": "FER-002",
        "price": 20,
        "category_id": category_id,
        **base_logistics,
        "weight_kg": 0.3,
    }
    response = client.post(
        "/products/", headers=superuser_token_headers, json=prod2_data
    )
    product_2_id = response.json()["id"]

    update_data = {"sku": "FER-001"}
    update_response = client.put(
        f"/products/{product_2_id}", headers=superuser_token_headers, json=update_data
    )
    assert update_response.status_code == 400
    assert "SKU já pertence a outro produto" in update_response.json()["detail"]


def test_create_product_with_nonexistent_category(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a criação de um produto com category_id inválida (espera 404)."""
    product_data = {
        "name": "Produto Órfão",
        "sku": "ORFAO-01",
        "price": 10.0,
        "category_id": 9999,
        "stock": 5,
        "weight_kg": 0.1,
        "height_cm": 1,
        "width_cm": 1,
        "length_cm": 1,
    }
    response = client.post(
        "/products/", headers=superuser_token_headers, json=product_data
    )
    assert response.status_code == 404, response.text
    assert "Categoria não encontrada" in response.json()["detail"]


def test_update_product_with_nonexistent_category(
    client: TestClient, superuser_token_headers: Dict
):
    """
    Testa a atualização de um produto para uma category_id inválida (espera 404).
    """
    category_id = create_category_and_get_id(
        client, superuser_token_headers, "Cat Original"
    )
    prod_data = {
        "name": "Produto a ser movido",
        "sku": "MOVER-01",
        "price": 50,
        "category_id": category_id,
        "weight_kg": 0.5,
        "height_cm": 5,
        "width_cm": 5,
        "length_cm": 5,
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    product_id = prod_resp.json()["id"]

    update_data = {"category_id": 9999}
    response = client.put(
        f"/products/{product_id}", headers=superuser_token_headers, json=update_data
    )
    assert response.status_code == 404, response.text
    assert "Categoria não encontrada" in response.json()["detail"]


def test_update_nonexistent_product(client: TestClient, superuser_token_headers: Dict):
    """Testa a falha ao tentar atualizar um produto com ID inexistente."""
    update_data = {"name": "Produto Fantasma", "price": 99.99}
    response = client.put(
        "/products/9999", headers=superuser_token_headers, json=update_data
    )
    assert response.status_code == 404
    assert "Produto não encontrado" in response.json()["detail"]


def test_delete_nonexistent_product(client: TestClient, superuser_token_headers: Dict):
    """Testa a falha ao tentar deletar um produto com ID inexistente."""
    response = client.delete("/products/9999", headers=superuser_token_headers)
    assert response.status_code == 404
    assert "Produto não encontrado" in response.json()["detail"]
