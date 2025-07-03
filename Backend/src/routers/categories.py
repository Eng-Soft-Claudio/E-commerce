"""
Módulo de Roteamento para o recurso 'Categoria'.

Define todos os endpoints da API relacionados a categorias, permitindo o CRUD
(Create, Read, Update, Delete). As operações de escrita (CUD) são protegidas
e exigem privilégios de administrador, enquanto a leitura é pública para que
os clientes possam navegar pelas categorias de produtos.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, crud, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                           ROUTER SETUP                                     #
# -------------------------------------------------------------------------- #

router = APIRouter(prefix="/categories", tags=["Categories"])

# -------------------------------------------------------------------------- #
#                        CATEGORY API ENDPOINTS (PROTEGIDOS)                 #
# -------------------------------------------------------------------------- #


@router.post(
    "/",
    response_model=schemas.Category,
    status_code=201,
    dependencies=[Depends(auth.get_current_superuser)],
)
def create_category_endpoint(
    category: schemas.CategoryCreate, db: Session = Depends(get_db)
):
    """[Admin] Cria uma nova categoria de produtos."""
    return crud.create_category(db=db, category=category)


@router.put(
    "/{category_id}",
    response_model=schemas.Category,
    dependencies=[Depends(auth.get_current_superuser)],
)
def update_category_endpoint(
    category_id: int, category: schemas.CategoryCreate, db: Session = Depends(get_db)
):
    """[Admin] Atualiza os dados de uma categoria existente."""
    db_category = crud.update_category(
        db, category_id=category_id, category_data=category
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return db_category


@router.delete(
    "/{category_id}",
    response_model=dict,
    dependencies=[Depends(auth.get_current_superuser)],
)
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    """[Admin] Deleta uma categoria do sistema."""
    db_category = crud.delete_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return {"message": "Categoria deletada com sucesso."}


# -------------------------------------------------------------------------- #
#                        CATEGORY API ENDPOINTS (PÚBLICOS)                   #
# -------------------------------------------------------------------------- #


@router.get("/", response_model=List[schemas.Category])
def read_categories_endpoint(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """[Público] Lista todas as categorias disponíveis."""
    categories = crud.get_categories(db, skip=skip, limit=limit)
    return categories


@router.get("/{category_id}", response_model=schemas.Category)
def read_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    """[Público] Busca uma única categoria pelo seu ID."""
    db_category = crud.get_category(db, category_id=category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return db_category
