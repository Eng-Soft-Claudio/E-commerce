"""
Módulo de Roteamento para o recurso 'Produto'.

Define todos os endpoints da API relacionados a produtos, incluindo operações
de CRUD (Create, Read, Update, Delete). As operações de escrita (CUD) são
protegidas e exigem privilégios de administrador, enquanto as operações
de leitura são públicas. A lógica de negócio, como a validação de SKU
duplicado, é implementada aqui.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth, crud, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                           ROUTER SETUP                                     #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={404: {"description": "Não encontrado"}},
)

# -------------------------------------------------------------------------- #
#                         PRODUCT API ENDPOINTS (PROTEGIDOS)                 #
# -------------------------------------------------------------------------- #


@router.post(
    "/",
    response_model=schemas.Product,
    status_code=201,
    dependencies=[Depends(auth.get_current_superuser)],
)
def create_product_endpoint(
    product: schemas.ProductCreate, db: Session = Depends(get_db)
):
    """
    [Admin] Cria um novo produto no catálogo.

    Requer privilégios de administrador. Antes da criação, verifica se a
    categoria fornecida existe e se o SKU (Stock Keeping Unit) já não está
    em uso por outro produto. Recebe e armazena os dados logísticos
    (peso e dimensões) do produto.
    """
    db_category = crud.get_category(db, category_id=product.category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    db_product_by_sku = crud.get_product_by_sku(db, sku=product.sku)
    if db_product_by_sku:
        raise HTTPException(status_code=400, detail="SKU já cadastrado.")

    return crud.create_product(db=db, product=product)


@router.put(
    "/{product_id}",
    response_model=schemas.Product,
    dependencies=[Depends(auth.get_current_superuser)],
)
def update_product_endpoint(
    product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    """
    [Admin] Atualiza um produto existente.

    Requer privilégios de administrador. Permite a atualização parcial dos
    dados do produto, incluindo seus dados logísticos. Se um novo SKU for
    fornecido, verifica se ele não está em uso por outro produto.
    """
    db_product = crud.get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    if product.sku and product.sku != db_product.sku:
        existing_product = crud.get_product_by_sku(db, sku=product.sku)
        if existing_product and existing_product.id != product_id:
            raise HTTPException(
                status_code=400, detail="SKU já pertence a outro produto."
            )

    if product.category_id:
        db_category = crud.get_category(db, category_id=product.category_id)
        if not db_category:
            raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    return crud.update_product(db, product_id=product_id, product_data=product)


@router.delete(
    "/{product_id}",
    response_model=dict,
    dependencies=[Depends(auth.get_current_superuser)],
)
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    """
    [Admin] Deleta um produto do catálogo.

    Requer privilégios de administrador. A operação é permanente e removerá o
    produto de futuras listagens.
    """
    db_product = crud.delete_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return {"message": "Produto deletado com sucesso."}


# -------------------------------------------------------------------------- #
#                          PRODUCT API ENDPOINTS (PÚBLICOS)                  #
# -------------------------------------------------------------------------- #


@router.get("/", response_model=List[schemas.Product])
def read_products_endpoint(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    q: Optional[str] = Query(None, description="Termo de busca para nome ou descrição"),
    db: Session = Depends(get_db),
):
    """
    [Público] Lista todos os produtos disponíveis no catálogo.

    Permite:
    - Paginação com `skip` e `limit`.
    - Filtragem por `category_id` para produtos de uma categoria específica.
    - Busca por um termo `q` no nome ou descrição dos produtos.
    """
    products = crud.get_products(
        db, skip=skip, limit=limit, category_id=category_id, q=q
    )
    return products


@router.get("/{product_id}", response_model=schemas.Product)
def read_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    """
    [Público] Busca um único produto pelo seu ID.
    """
    db_product = crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return db_product
