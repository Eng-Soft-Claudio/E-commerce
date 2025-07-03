"""
Testes Unitários para o Módulo CRUD.

Estes testes focam em cobrir os casos de borda das funções CRUD
que são difíceis de acionar através dos endpoints da API, como retornos
`None` explícitos e manipulação direta de objetos do DB.
"""
# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
import pytest
from unittest.mock import patch

from src import crud, schemas
from src.schemas import ProductUpdate

# -------------------------------------------------------------------------- #
#                             FIXTURES                                       #
# -------------------------------------------------------------------------- #
pytestmark = pytest.mark.usefixtures("db_session")

# -------------------------------------------------------------------------- #
#                             TESTES UNITÁRIOS                               #
# -------------------------------------------------------------------------- #
def test_crud_update_product_not_found(db_session):
    """Testa update_product retornando None quando o produto não é encontrado."""
    product_update_data = ProductUpdate(name="Nome Fantasma")
    result = crud.update_product(
        db_session, product_id=999, product_data=product_update_data
    )
    assert result is None


def test_add_item_to_cart_product_not_found(db_session):
    """Testa add_item_to_cart retornando None quando o produto não existe."""
    item_create = schemas.CartItemCreate(product_id=9999, quantity=1)
    result = crud.add_item_to_cart(db_session, cart_id=1, item=item_create)
    assert result is None


@patch("src.crud.remove_cart_item")
def test_update_cart_item_quantity_less_than_zero(mock_remove, db_session):
    """Testa se update_cart_item_quantity chama remove_cart_item quando a quantidade é <= 0."""
    crud.update_cart_item_quantity(db_session, cart_id=1, product_id=1, quantity=0)
    mock_remove.assert_called_once_with(db_session, cart_id=1, product_id=1)

    crud.update_cart_item_quantity(db_session, cart_id=1, product_id=1, quantity=-5)
    assert mock_remove.call_count == 2
    mock_remove.assert_called_with(db_session, cart_id=1, product_id=1)


def test_crud_delete_category_not_found(db_session):
    """Testa delete_category retornando None para um id inexistente."""
    result = crud.delete_category(db_session, 999)
    assert result is None
