"""
Módulo de Roteamento para Autenticação e Gerenciamento de Usuários.

Define os endpoints públicos para registro de novos usuários, para
obtenção de tokens de acesso (login) e os endpoints para que um usuário
autenticado gerencie seu próprio perfil.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import auth, crud, models, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# -------------------------------------------------------------------------- #
#                        AUTHENTICATION API ENDPOINTS                        #
# -------------------------------------------------------------------------- #


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Endpoint de login para obter um token de acesso.

    Este endpoint segue o fluxo do OAuth2 'Password Flow'. Ele recebe as
    credenciais do usuário (email como 'username' e a senha) em um formulário,
    verifica se são válidas e, em caso afirmativo, retorna um token JWT.

    Args:
        db (Session): A sessão do banco de dados.
        form_data (OAuth2PasswordRequestForm): Formulário com 'username' e 'password'.

    Raises:
        HTTPException(401): Se as credenciais forem inválidas.

    Returns:
        schemas.Token: O token de acesso JWT e o tipo de token ('bearer').
    """
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/users/", response_model=schemas.User, status_code=201)
def create_user_endpoint(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Cria um novo usuário (registro público).

    Verifica se o email já existe no sistema antes de criar um novo
    registro de usuário.

    Args:
        user (schemas.UserCreate): Os dados do novo usuário.
        db (Session): A sessão do banco de dados.

    Raises:
        HTTPException(400): Se o email já estiver registrado.

    Returns:
        schemas.User: O usuário recém-criado (sem a senha).
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)
):
    """
    Inicia o fluxo de recuperação de senha para um usuário.
    Se o usuário existir, um token é gerado e salvo.
    """
    user = crud.get_user_by_email(db, email=request.email)
    if user:
        reset_token = auth.create_password_reset_token()
        crud.create_password_reset_token(db, email=user.email, token=reset_token)
        print(f"Password reset token for {user.email}: {reset_token}")
        return {
            "detail": "If an account with this email exists, a password reset link has been sent.",
            "token": reset_token,
        }

    return {
        "detail": "If an account with this email exists, a password reset link has been sent."
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)
):
    """
    Finaliza o fluxo de recuperação de senha, definindo uma nova senha.
    """
    user = crud.get_user_by_password_reset_token(db, token=request.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperação inválido ou expirado.",
        )

    crud.update_user_password(db, user=user, new_password=request.new_password)

    return {"message": "Senha atualizada com sucesso."}


# -------------------------------------------------------------------------- #
#                             USER PROFILE ENDPOINT                          #
# -------------------------------------------------------------------------- #


@router.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    Retorna os dados do usuário atualmente logado.

    Utiliza a dependência get_current_user para identificar e retornar
    as informações do usuário que fez a requisição.
    """
    return current_user


@router.put("/users/me/", response_model=schemas.User)
def update_user_me(
    user_data: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Atualiza os dados de perfil do usuário atualmente logado.

    Recebe os dados parciais no corpo da requisição e atualiza apenas os
    campos fornecidos. Garante que um usuário só pode modificar o próprio
    perfil.

    Args:
        user_data (schemas.UserUpdate): Os dados a serem atualizados.
        current_user (models.User): O usuário logado, injetado pela dependência.
        db (Session): A sessão do banco de dados.

    Returns:
        schemas.User: Os dados atualizados do usuário.
    """
    updated_user = crud.update_user_profile(
        db=db, user=current_user, user_data=user_data
    )
    return updated_user


@router.put("/users/me/password", status_code=status.HTTP_200_OK)
def update_user_password_me(
    request: schemas.UpdatePasswordRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Atualiza a senha do usuário atualmente logado.

    Este endpoint requer que o usuário forneça sua senha atual por motivos de
    segurança. Se a senha atual estiver correta, a nova senha será hasheada
    e salva no banco de dados.

    Args:
        request (schemas.UpdatePasswordRequest): Corpo da requisição com a
                                                 senha atual e a nova senha.
        current_user (models.User): O usuário logado, injetado pela dependência.
        db (Session): A sessão do banco de dados.

    Raises:
        HTTPException(400): Se a senha atual fornecida estiver incorreta.

    Returns:
        dict: Uma mensagem confirmando que a senha foi atualizada com sucesso.
    """
    if not auth.verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password.",
        )

    crud.update_user_password(db, user=current_user, new_password=request.new_password)

    return {"message": "Password updated successfully."}
