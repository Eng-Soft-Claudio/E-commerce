"""
Módulo de Roteamento para Gerenciamento de Usuários (Admin).

Define os endpoints que permitem a um administrador realizar operações
completas de CRUD (Create, Read, Update, Delete) nos usuários da plataforma.
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
router = APIRouter(
    prefix="/admin/users",
    tags=["Admin: Users"],
    dependencies=[Depends(auth.get_current_superuser)],
)


# -------------------------------------------------------------------------- #
#                  ENDPOINTS DE GERENCIAMENTO DE USUÁRIOS (Admin)            #
# -------------------------------------------------------------------------- #
@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    [Admin] Retorna uma lista de todos os usuários (clientes) do sistema.

    Este endpoint é protegido e requer privilégios de superusuário.
    Ele utiliza paginação para lidar com um grande número de usuários.
    """
    users = crud.get_all_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    [Admin] Retorna os dados de um único usuário pelo seu ID.
    """
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.User)
def update_user_by_admin(
    user_id: int, user_data: schemas.AdminUserUpdate, db: Session = Depends(get_db)
):
    """
    [Admin] Atualiza os dados de um usuário pelo seu ID.

    Permite a um administrador modificar informações de perfil, o status de
    `is_active` e o status de `is_superuser`.
    """
    updated_user = crud.update_user_by_admin(db, user_id=user_id, user_data=user_data)
    if not updated_user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    [Admin] Deleta permanentemente um usuário pelo seu ID.

    Impede que um administrador delete a sua própria conta.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As an administrator, you cannot delete your own account.",
        )

    user_to_delete = crud.delete_user(db, user_id=user_id)
    if not user_to_delete:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"message": "User deleted successfully."}
