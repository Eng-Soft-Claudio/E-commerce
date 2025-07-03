"""
Módulo de Roteamento para Pedidos (Orders).

Define os endpoints para criar e visualizar os pedidos de um usuário. A rota de
criação é o ponto final do ciclo de compra, onde a verificação de estoque final
e o débito são realizados de forma transacional. Inclui também endpoints
protegidos para administradores gerenciarem todos os pedidos.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from .. import auth, crud, models, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                           ROUTER SETUP                                     #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    dependencies=[Depends(auth.get_current_user)],
)

# -------------------------------------------------------------------------- #
#                       SCHEMAS ESPECÍFICOS PARA ESTA ROTA                   #
# -------------------------------------------------------------------------- #


class StatusUpdate(BaseModel):
    """Schema para receber a atualização de status no corpo da requisição PUT."""

    status: str


# -------------------------------------------------------------------------- #
#                          ENDPOINTS PARA CLIENTES                           #
# -------------------------------------------------------------------------- #


@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cria um novo pedido a partir do carrinho atual do usuário.

    Este é um endpoint crítico que executa a lógica transacional de
    verificação de estoque, criação do pedido e esvaziamento do carrinho.
    Qualquer falha, como estoque insuficiente, reverte todas as operações.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusuários não podem criar pedidos.",
        )
    try:
        order = crud.create_order_from_cart(db, user=current_user)
        return order
    except crud.OrderCreationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/", response_model=List[schemas.Order])
def read_my_orders(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna o histórico de todos os pedidos feitos pelo usuário atual."""
    return crud.get_orders_by_user(db, user_id=current_user.id)


@router.get("/{order_id}", response_model=schemas.Order)
def read_single_order(
    order_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Busca e retorna um único pedido pelo seu ID.

    Um usuário comum só pode ver seus próprios pedidos. Um superusuário
    pode ver qualquer pedido.
    """
    order = crud.get_order_by_id(db, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado."
        )
    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não autorizado a visualizar este pedido.",
        )
    return order


# -------------------------------------------------------------------------- #
#                        ENDPOINTS PARA ADMINISTRADORES                      #
# -------------------------------------------------------------------------- #


@router.get(
    "/admin/all",
    response_model=List[schemas.AdminOrder],
    dependencies=[Depends(auth.get_current_superuser)],
)
def read_all_orders_admin(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """[Admin] Retorna uma lista de todos os pedidos no sistema."""
    orders = crud.get_all_orders(db, skip=skip, limit=limit)
    return orders


@router.put(
    "/{order_id}/status",
    response_model=schemas.AdminOrder,
    dependencies=[Depends(auth.get_current_superuser)],
)
def update_order_status_admin(
    order_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)
):
    """[Admin] Atualiza o status de um pedido específico."""
    order_in_db = crud.get_order_by_id(db, order_id=order_id)
    if not order_in_db:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    allowed_statuses = ["pending_payment", "paid", "shipped", "delivered", "cancelled"]
    if status_update.status not in allowed_statuses:
        raise HTTPException(
            status_code=400, detail=f"Status '{status_update.status}' é inválido."
        )

    order_in_db.status = status_update.status
    db.commit()

    reloaded_order = (
        db.query(models.Order)
        .options(
            joinedload(models.Order.customer),
            joinedload(models.Order.items).joinedload(models.OrderItem.product),
        )
        .filter(models.Order.id == order_id)
        .first()
    )

    if not reloaded_order:
        raise HTTPException(
            status_code=500, detail="Falha ao recarregar o pedido após a atualização."
        )

    return reloaded_order
