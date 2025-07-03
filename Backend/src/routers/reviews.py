"""
Módulo de Roteamento para o recurso 'Avaliação de Produto' (Reviews).

Define os endpoints da API para criar, ler e deletar avaliações de produtos.
A criação é restrita a usuários logados, a leitura é pública e a remoção
é restrita a administradores.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, crud, models, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(tags=["Product Reviews"])


# -------------------------------------------------------------------------- #
#                       PRODUCT REVIEWS API ENDPOINTS                        #
# -------------------------------------------------------------------------- #


@router.post(
    "/products/{product_id}/reviews",
    response_model=schemas.ProductReview,
    status_code=status.HTTP_201_CREATED,
)
def create_review_for_product(
    product_id: int,
    review: schemas.ProductReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    [Logado] Cria uma nova avaliação para um produto específico.

    Um usuário só pode avaliar um produto uma única vez. Se tentar
    avaliar novamente, receberá um erro 409 (Conflict).

    Args:
        product_id (int): O ID do produto a ser avaliado.
        review (schemas.ProductReviewCreate): Os dados da avaliação.
        db (Session): A sessão do banco de dados.
        current_user (models.User): O usuário autenticado.

    Raises:
        HTTPException 404: Se o produto não for encontrado.
        HTTPException 409: Se o usuário já tiver avaliado este produto.
    """
    db_product = crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado."
        )

    try:
        return crud.create_product_review(
            db=db, review_data=review, user_id=current_user.id, product_id=product_id
        )
    except crud.ReviewCreationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/products/{product_id}/reviews", response_model=List[schemas.ProductReview]
)
def read_reviews_for_product(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """[Público] Lista todas as avaliações de um produto específico."""
    db_product = crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado."
        )
    reviews = crud.get_reviews_by_product(
        db, product_id=product_id, skip=skip, limit=limit
    )
    return reviews


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth.get_current_superuser)],
)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    """[Admin] Deleta uma avaliação específica pelo seu ID."""
    db_review = crud.delete_product_review(db, review_id=review_id)
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação não encontrada."
        )
    return {"message": "Avaliação deletada com sucesso."}
