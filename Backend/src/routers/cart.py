"""
Módulo de Roteamento para o Carrinho de Compras do Usuário.

Define todos os endpoints da API para visualizar e manipular o carrinho de
compras de um usuário autenticado. Todas as rotas neste módulo exigem um
usuário logado para serem acessadas e implementam validações de permissão e
estoque antes de qualquer operação no banco de dados.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, crud, models, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                           ROUTER SETUP                                     #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/cart",
    tags=["Shopping Cart"],
    dependencies=[Depends(auth.get_current_user)],
)


# -------------------------------------------------------------------------- #
#                        SHOPPING CART API ENDPOINTS                         #
# -------------------------------------------------------------------------- #


@router.get("/", response_model=schemas.Cart)
def read_my_cart(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retorna o carrinho de compras do usuário. Cria um se não existir.
    Superusuários são proibidos de acessar esta rota.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusuários não possuem carrinho de compras.",
        )
    cart = crud.get_cart_by_user_id(db, user_id=current_user.id)
    if not cart:
        cart = models.Cart(owner=current_user)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.post("/items/", response_model=schemas.CartItem)
def add_product_to_cart(
    item: schemas.CartItemCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Adiciona um produto ao carrinho ou atualiza sua quantidade.
    Verifica permissão, existência do produto e estoque disponível.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusuários não podem adicionar itens ao carrinho.",
        )
    cart = crud.get_cart_by_user_id(db, current_user.id)
    if not cart:
        raise HTTPException(
            status_code=404, detail="Carrinho do usuário não encontrado."
        )
    db_product = crud.get_product(db, product_id=item.product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    db_cart_item = crud.add_item_to_cart(db, cart_id=cart.id, item=item)
    if not db_cart_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Estoque insuficiente."
        )

    return db_cart_item


@router.put("/items/{product_id}", response_model=schemas.CartItem)
def update_cart_item(
    product_id: int,
    item_update: schemas.CartItemUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Atualiza a quantidade de um item específico no carrinho do usuário.
    Verifica permissão e estoque disponível.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusuários não podem modificar carrinhos.",
        )

    cart = crud.get_cart_by_user_id(db, current_user.id)
    if not cart:
        raise HTTPException(
            status_code=404, detail="Carrinho do usuário não encontrado."
        )

    if item_update.quantity <= 0:
        crud.remove_cart_item(db, cart_id=cart.id, product_id=product_id)
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    updated_item = crud.update_cart_item_quantity(
        db, cart_id=cart.id, product_id=product_id, quantity=item_update.quantity
    )
    if not updated_item:
        raise HTTPException(
            status_code=404,
            detail="Item não encontrado no carrinho ou estoque insuficiente.",
        )

    return updated_item


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product_from_cart(
    product_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Remove um produto específico do carrinho do usuário atual."""
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusuários não podem remover itens do carrinho.",
        )

    cart = crud.get_cart_by_user_id(db, current_user.id)
    if not cart:
        raise HTTPException(
            status_code=404, detail="Carrinho do usuário não encontrado."
        )

    item_removed = crud.remove_cart_item(db, cart_id=cart.id, product_id=product_id)
    if not item_removed:
        raise HTTPException(
            status_code=404, detail="Produto não encontrado no carrinho."
        )


# -------------------------------------------------------------------------- #
#                        COUPON APPLICATION ENDPOINTS                        #
# -------------------------------------------------------------------------- #


@router.post("/apply-coupon", response_model=schemas.Cart)
def apply_coupon(
    request: schemas.ApplyCouponRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Aplica um cupom de desconto ao carrinho do usuário."""
    cart = crud.get_cart_by_user_id(db, user_id=current_user.id)
    if not cart:
        raise HTTPException(status_code=404, detail="Carrinho não encontrado.")

    coupon = crud.get_valid_coupon_by_code(db, code=request.code)
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupom inválido ou expirado.")

    updated_cart = crud.apply_coupon_to_cart(db, cart, coupon)
    return updated_cart


@router.delete("/apply-coupon", response_model=schemas.Cart)
def remove_coupon(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Remove o cupom de desconto aplicado ao carrinho do usuário."""
    cart = crud.get_cart_by_user_id(db, user_id=current_user.id)
    if not cart:
        raise HTTPException(status_code=404, detail="Carrinho não encontrado.")

    if not cart.coupon:
        return cart

    updated_cart = crud.remove_coupon_from_cart(db, cart)
    return updated_cart
