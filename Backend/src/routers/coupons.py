"""
Módulo de Roteamento para o recurso 'Cupom de Desconto' (Admin).

Define endpoints protegidos para administradores realizarem operações de CRUD
(Criar, Ler, Atualizar, Deletar) nos cupons de desconto.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import auth, crud, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/coupons",
    tags=["Admin: Coupons"],
    dependencies=[Depends(auth.get_current_superuser)],
)

# -------------------------------------------------------------------------- #
#                        COUPON API ENDPOINTS (ADMIN)                        #
# -------------------------------------------------------------------------- #


@router.post("/", response_model=schemas.Coupon, status_code=status.HTTP_201_CREATED)
def create_coupon_endpoint(coupon: schemas.CouponCreate, db: Session = Depends(get_db)):
    """[Admin] Cria um novo cupom de desconto."""
    try:
        return crud.create_coupon(db, coupon_data=coupon)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Um cupom com este código já existe.",
        )


@router.get("/", response_model=List[schemas.Coupon])
def read_coupons_endpoint(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """[Admin] Lista todos os cupons de desconto."""
    return crud.get_coupons(db, skip=skip, limit=limit)


@router.put("/{coupon_id}", response_model=schemas.Coupon)
def update_coupon_endpoint(
    coupon_id: int, coupon: schemas.CouponUpdate, db: Session = Depends(get_db)
):
    """[Admin] Atualiza um cupom de desconto existente."""
    db_coupon = crud.update_coupon(db, coupon_id=coupon_id, coupon_data=coupon)
    if not db_coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cupom não encontrado."
        )
    return db_coupon


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coupon_endpoint(coupon_id: int, db: Session = Depends(get_db)):
    """[Admin] Deleta um cupom de desconto."""
    db_coupon = crud.delete_coupon(db, coupon_id=coupon_id)
    if not db_coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cupom não encontrado."
        )
