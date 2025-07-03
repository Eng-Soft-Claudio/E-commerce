"""
Módulo de Autenticação e Segurança.

Contém toda a lógica para hashing de senhas, criação e verificação
de tokens JWT, e as dependências do FastAPI para proteger endpoints.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import crud, models
from .database import get_db
from .settings import settings

# -------------------------------------------------------------------------- #
#                         CONFIGURAÇÕES DE SEGURANÇA                         #
# -------------------------------------------------------------------------- #

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


# -------------------------------------------------------------------------- #
#                      FUNÇÕES UTILITÁRIAS DE SENHA E TOKEN                  #
# -------------------------------------------------------------------------- #


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde a um hash.

    Args:
        plain_password (str): A senha fornecida pelo usuário.
        hashed_password (str): A senha armazenada no banco de dados.

    Returns:
        bool: True se as senhas corresponderem, False caso contrário.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera o hash de uma senha em texto plano.

    Args:
        password (str): A senha a ser hasheada.

    Returns:
        str: A versão hasheada da senha.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Cria um novo token de acesso JWT.

    O payload do token inclui o 'subject' (sub) e uma data de expiração (exp).

    Args:
        data (dict): Dados a serem incluídos no payload do token (ex: {'sub': email}).
        expires_delta (Optional[timedelta]): Duração de validade do token.

    Returns:
        str: O token de acesso JWT codificado.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_password_reset_token() -> str:
    """Gera um token criptograficamente seguro para o reset de senha."""
    return secrets.token_urlsafe(32)


# -------------------------------------------------------------------------- #
#                        DEPENDÊNCIAS DE AUTENTICAÇÃO                        #
# -------------------------------------------------------------------------- #


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    """
    Dependência FastAPI para obter o usuário atual a partir de um token JWT.

    Esta função é injetada em endpoints para garantir que a requisição
    seja feita por um usuário autenticado e válido.

    Args:
        db (Session): A sessão do banco de dados.
        token (str): O token de acesso Bearer fornecido no header da requisição.

    Raises:
        HTTPException(401): Se o token for inválido, expirado ou o usuário
                           não for encontrado.

    Returns:
        models.User: O objeto de usuário do SQLAlchemy correspondente ao token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependência FastAPI para garantir que o usuário atual seja um superuser.

    Esta dependência reutiliza `get_current_user` e adiciona uma verificação
    adicional no campo `is_superuser`. Deve ser usada para proteger endpoints
    que só podem ser acessados por administradores.

    Args:
        current_user (models.User): O usuário obtido pela dependência `get_current_user`.

    Raises:
        HTTPException(403): Se o usuário não for um superuser.

    Returns:
        models.User: O objeto do usuário se ele for um superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
