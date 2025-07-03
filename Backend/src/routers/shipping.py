"""
Módulo de Roteamento para Frete.

Define os endpoints da API relacionados ao cálculo de frete, atuando como
uma ponte entre a requisição do cliente e o serviço de logística externo.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import List, Dict, Any  # noqa: F401

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from .. import auth, crud, models
from ..database import get_db
from ..services.shipping_service import (
    calculate_shipping_options,
    ShippingCalculationError,
)

# -------------------------------------------------------------------------- #
#                             SCHEMAS ESPECÍFICOS                            #
# -------------------------------------------------------------------------- #


class ShippingRequest(BaseModel):
    """Schema para o corpo da requisição de cálculo de frete."""

    postal_code: str = Field(..., pattern=r"^\d{5}-?\d{3}$")


class ShippingOption(BaseModel):
    """Schema para a resposta de uma opção de frete."""

    name: str
    price: float
    delivery_time: int
    company: str | None


# -------------------------------------------------------------------------- #
#                           ROUTER SETUP                                     #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/shipping",
    tags=["Shipping"],
    dependencies=[Depends(auth.get_current_user)],
)

# -------------------------------------------------------------------------- #
#                          SHIPPING API ENDPOINTS                            #
# -------------------------------------------------------------------------- #


@router.post(
    "/calculate",
    response_model=List[ShippingOption],
    summary="Calcula as opções de frete para o carrinho atual",
)
def calculate_shipping(
    request: ShippingRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Calcula as opções de frete disponíveis (ex: PAC, SEDEX) para o carrinho
    de compras do usuário atual com base no CEP de destino fornecido.

    Este endpoint obtém o carrinho do usuário, valida se não está vazio e
    invoca o serviço de cálculo de frete, que por sua vez se comunica com a
    API externa da Melhor Envio.

    Args:
        request (ShippingRequest): Corpo da requisição contendo o CEP de destino.
        current_user (models.User): O usuário autenticado, injetado pela dependência.
        db (Session): A sessão do banco de dados.

    Raises:
        HTTPException(404): Se o carrinho do usuário não for encontrado.
        HTTPException(400): Se o carrinho estiver vazio.
        HTTPException(variável): Propaga erros da camada de serviço, como falhas
                                 de comunicação ou validação da API de frete.

    Returns:
        List[ShippingOption]: Uma lista de opções de frete com seus respectivos
                              nomes, preços, e prazos de entrega.
    """
    cart = crud.get_cart_by_user_id(db, user_id=current_user.id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Carrinho não encontrado."
        )
    if not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível calcular o frete para um carrinho vazio.",
        )

    try:
        shipping_options = calculate_shipping_options(
            destination_postal_code=request.postal_code, items=cart.items
        )
        return shipping_options

    except ShippingCalculationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
