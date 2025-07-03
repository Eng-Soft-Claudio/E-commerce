"""
Módulo de Serviço para Cálculo de Frete.

Este módulo encapsula toda a lógica de comunicação com a API externa da
plataforma Melhor Envio para realizar a cotação de frete. Ele é responsável
por:
1.  Preparar o payload da requisição, incluindo a lógica de "empacotamento"
    dos itens do carrinho para determinar o peso e dimensões finais.
2.  Construir e enviar a requisição HTTP para o endpoint da Melhor Envio.
3.  Tratar a resposta (JSON), formatando-a de maneira clara para ser consumida
    pela nossa API.
4.  Gerenciar a autenticação e os erros de comunicação com a API externa.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
import logging
from typing import List, Dict, Any, Tuple

import requests
from requests.exceptions import RequestException

from .. import models
from ..settings import settings

# -------------------------------------------------------------------------- #
#                            CONFIGURAÇÃO E CONSTANTES                       #
# -------------------------------------------------------------------------- #

log = logging.getLogger(__name__)

MELHOR_ENVIO_API_URL = "https://sandbox.melhorenvio.com.br/api/v2/me/shipment/calculate"

MIN_HEIGHT_CM = 1.0
MIN_WIDTH_CM = 10.0
MIN_LENGTH_CM = 15.0
MIN_WEIGHT_KG = 0.05

# -------------------------------------------------------------------------- #
#                         EXCEÇÕES CUSTOMIZADAS                              #
# -------------------------------------------------------------------------- #


class ShippingCalculationError(Exception):
    """Exceção customizada para erros durante o cálculo de frete."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# -------------------------------------------------------------------------- #
#                                FUNÇÕES DE LÓGICA                           #
# -------------------------------------------------------------------------- #


def _prepare_package_for_api(
    items: List[models.CartItem],
) -> Tuple[Dict[str, Any], float]:
    """
    Prepara os dados do pacote para a API da Melhor Envio.

    Esta função implementa a lógica de "empacotamento virtual". Ela recebe
    os itens do carrinho, calcula o peso total e as dimensões consolidadas do
    pacote. Uma heurística comum e simples é usada para as dimensões:
    - O peso é a soma dos pesos de todos os produtos (vezes a quantidade).
    - A altura final é a soma das alturas de todos os produtos empilhados.
    - A largura e o comprimento são os maiores valores entre todos os produtos.

    Garante também que as dimensões e o peso atendam aos mínimos exigidos.

    Args:
        items (List[models.CartItem]): A lista de itens do carrinho.

    Returns:
        Tuple[Dict[str, Any], float]: Uma tupla contendo o dicionário do pacote
        pronto para a API e o valor total dos produtos (seguro).
    """
    if not items:
        return {}, 0.0

    total_weight = sum(item.product.weight_kg * item.quantity for item in items)
    total_value = sum(item.product.price * item.quantity for item in items)

    final_height = sum(item.product.height_cm * item.quantity for item in items)
    final_width = max(item.product.width_cm for item in items)
    final_length = max(item.product.length_cm for item in items)

    package = {
        "weight": max(total_weight, MIN_WEIGHT_KG),
        "height": max(final_height, MIN_HEIGHT_CM),
        "width": max(final_width, MIN_WIDTH_CM),
        "length": max(final_length, MIN_LENGTH_CM),
    }

    return package, total_value


def calculate_shipping_options(
    destination_postal_code: str, items: List[models.CartItem]
) -> List[Dict[str, Any]]:
    """
    Calcula as opções de frete para um determinado CEP e lista de itens.

    Args:
        destination_postal_code (str): O CEP de destino do cliente.
        items (List[models.CartItem]): A lista de itens do carrinho de compras.

    Raises:
        ShippingCalculationError: Se a comunicação com a API falhar ou
                                  se a API retornar um erro de validação.

    Returns:
        List[Dict[str, Any]]: Uma lista de dicionários, onde cada um representa
                              uma opção de frete com nome, preço e prazo.
    """
    package, total_value = _prepare_package_for_api(items)
    if not package:
        return []

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.MELHOR_ENVIO_TOKEN}",
        "User-Agent": "LouvaDeus E-commerce (contato@louva-deus.com)",
    }

    payload = {
        "from": {"postal_code": settings.STORE_ORIGIN_CEP},
        "to": {"postal_code": destination_postal_code.replace("-", "")},
        "package": package,
        "options": {
            "insurance_value": total_value,
            "receipt": False,
            "own_hand": False,
        },
        "services": "1,2",  # Correios: 1=SEDEX, 2=PAC
    }

    try:
        response = requests.post(
            MELHOR_ENVIO_API_URL, json=payload, headers=headers, timeout=10
        )
        response.raise_for_status()

    except RequestException as e:
        log.error(f"Erro de comunicação com a API Melhor Envio: {e}")
        raise ShippingCalculationError(
            "Falha na comunicação com o serviço de frete.", status_code=503
        ) from e

    data = response.json()

    if "errors" in data:
        log.error(f"Erro retornado pela API Melhor Envio: {data['errors']}")
        error_message = data["errors"].popitem()[1][0]  
        raise ShippingCalculationError(
            f"Erro ao calcular o frete: {error_message}", status_code=400
        )

    available_options = [
        {
            "name": option["name"],
            "price": float(option["price"]),
            "delivery_time": option["delivery_time"],
            "company": option.get("company", {}).get("name"),
        }
        for option in data
        if "error" not in option
    ]

    return available_options
