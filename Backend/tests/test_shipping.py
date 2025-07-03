"""
Suíte de Testes para o recurso de Cálculo de Frete.

Testa o endpoint sob o prefixo `/shipping`, cobrindo:
- A validação da requisição (ex: carrinho vazio).
- O tratamento de sucesso ao receber opções de frete.
- A simulação (mock) de respostas de erro da API da Melhor Envio.
- O controle de acesso, garantindo que apenas usuários logados podem cotar.
- A lógica de empacotamento virtual de múltiplos produtos.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

import pytest
from typing import Dict, Any, List
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from requests.exceptions import HTTPError, RequestException

# -------------------------------------------------------------------------- #
#                             FIXTURES AUXILIARES                            #
# -------------------------------------------------------------------------- #


@pytest.fixture
def products_for_shipping(
    client: TestClient, superuser_token_headers: Dict
) -> List[Dict[str, Any]]:
    """
    Cria uma categoria e dois produtos com dados logísticos para os testes
    de cálculo de frete. Retorna uma lista com os dicionários dos produtos criados.
    """
    cat_resp = client.post(
        "/categories/",
        headers=superuser_token_headers,
        json={"title": "Categoria Frete"},
    )
    cat_resp.raise_for_status()
    category_id = cat_resp.json()["id"]

    products_data = [
        {
            "sku": "PROD-SHIP-A",
            "name": "Produto A para Frete",
            "price": 50.0,
            "category_id": category_id,
            "stock": 10,
            "weight_kg": 0.5,
            "height_cm": 5,
            "width_cm": 15,
            "length_cm": 20,
        },
        {
            "sku": "PROD-SHIP-B",
            "name": "Produto B para Frete",
            "price": 100.0,
            "category_id": category_id,
            "stock": 5,
            "weight_kg": 1.2,
            "height_cm": 10,
            "width_cm": 25,
            "length_cm": 30,
        },
    ]

    created_products = []
    for data in products_data:
        prod_resp = client.post(
            "/products/", headers=superuser_token_headers, json=data
        )
        prod_resp.raise_for_status()
        created_products.append(prod_resp.json())

    return created_products


def _mock_shipping_api(mocker, json_response: Any, status_code: int = 200):
    """
    Função auxiliar para mockar a resposta da API de frete.
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_response

    if status_code >= 400:
        mock_response.raise_for_status.side_effect = HTTPError(
            "Mocked HTTP Error", response=mock_response
        )
    else:
        mock_response.raise_for_status.return_value = None

    mocker.patch("requests.post", return_value=mock_response)
    return mock_response


# -------------------------------------------------------------------------- #
#                    TESTES DE LÓGICA E CONTROLE DE ACESSO                   #
# -------------------------------------------------------------------------- #


def test_calculate_shipping_unauthenticated(client: TestClient):
    """Testa se um cliente não autenticado é bloqueado de calcular o frete."""
    response = client.post("/shipping/calculate", json={"postal_code": "12345-678"})
    assert response.status_code == 401


def test_calculate_shipping_with_empty_cart(
    client: TestClient, user_token_headers: Dict
):
    """Testa a falha ao tentar calcular o frete para um carrinho vazio."""
    response = client.post(
        "/shipping/calculate",
        headers=user_token_headers,
        json={"postal_code": "12345-678"},
    )
    assert response.status_code == 400
    assert "carrinho vazio" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                    TESTES DE SUCESSO E MOCK DA API EXTERNA                 #
# -------------------------------------------------------------------------- #


def test_calculate_shipping_success(
    client: TestClient,
    user_token_headers: Dict,
    products_for_shipping: List[Dict],
    mocker,
):
    """
    Testa o fluxo de sucesso completo: popula o carrinho, chama o endpoint
    de cálculo e verifica se a resposta mockada é retornada corretamente.
    """
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": products_for_shipping[0]["id"], "quantity": 1},
    ).raise_for_status()

    mock_api_response = [
        {
            "id": 1,
            "name": "SEDEX",
            "price": "35.50",
            "delivery_time": 3,
            "company": {"name": "Correios", "picture": "url..."},
        },
        {
            "id": 2,
            "name": "PAC",
            "price": "22.10",
            "delivery_time": 7,
            "company": {"name": "Correios", "picture": "url..."},
        },
    ]
    _mock_shipping_api(mocker, json_response=mock_api_response, status_code=200)

    response = client.post(
        "/shipping/calculate",
        headers=user_token_headers,
        json={"postal_code": "99999-888"},
    )

    assert response.status_code == 200, response.text
    shipping_options = response.json()
    assert len(shipping_options) == 2
    assert shipping_options[0]["name"] == "SEDEX"
    assert shipping_options[0]["price"] == 35.50
    assert shipping_options[1]["name"] == "PAC"
    assert shipping_options[1]["company"] == "Correios"


def test_calculate_shipping_for_multiple_items(
    client: TestClient,
    user_token_headers: Dict,
    products_for_shipping: List[Dict],
    mocker,
):
    """
    Testa se a lógica de empacotamento virtual funciona ao adicionar
    múltiplos itens ao carrinho e chamar a cotação.
    """
    for product in products_for_shipping:
        client.post(
            "/cart/items/",
            headers=user_token_headers,
            json={"product_id": product["id"], "quantity": 1},
        ).raise_for_status()

    mock_api_response = [
        {
            "name": "Entrega Combinada",
            "price": "50.00",
            "delivery_time": 5,
            "company": {"name": "Jadlog"},
        }
    ]
    _mock_shipping_api(mocker, mock_api_response)

    response = client.post(
        "/shipping/calculate",
        headers=user_token_headers,
        json={"postal_code": "11111-222"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Entrega Combinada"


# -------------------------------------------------------------------------- #
#                        TESTES DE TRATAMENTO DE ERROS                       #
# -------------------------------------------------------------------------- #


def test_shipping_calculation_handles_api_validation_error(
    client: TestClient,
    user_token_headers: Dict,
    products_for_shipping: List[Dict],
    mocker,
):
    """
    Testa se a nossa API trata corretamente um erro de validação (ex: CEP inválido)
    retornado pela API da Melhor Envio.
    """
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": products_for_shipping[0]["id"], "quantity": 1},
    ).raise_for_status()

    mock_api_error = {"errors": {"to": ["O CEP de destino é inválido."]}}

    mocked_response = _mock_shipping_api(
        mocker, json_response=mock_api_error, status_code=422
    )
    mocked_response.raise_for_status.side_effect = None

    response = client.post(
        "/shipping/calculate",
        headers=user_token_headers,
        json={"postal_code": "00000-000"},
    )

    assert response.status_code == 400, response.text
    assert "O CEP de destino é inválido" in response.json()["detail"]


def test_shipping_calculation_handles_api_communication_error(
    client: TestClient,
    user_token_headers: Dict,
    products_for_shipping: List[Dict],
    mocker,
):
    """
    Testa se nossa API trata um erro de comunicação (ex: timeout, 503)
    ao tentar se conectar com a API da Melhor Envio.
    """
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": products_for_shipping[0]["id"], "quantity": 1},
    ).raise_for_status()

    mocker.patch("requests.post", side_effect=RequestException("Network error"))

    response = client.post(
        "/shipping/calculate",
        headers=user_token_headers,
        json={"postal_code": "12345-678"},
    )

    assert response.status_code == 503, response.text
    assert "Falha na comunicação com o serviço de frete" in response.json()["detail"]
