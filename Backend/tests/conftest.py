"""
Arquivo de Configuração Central do Pytest (Conftest).

Este arquivo define fixtures essenciais utilizadas em toda a suíte de testes.
Ele é responsável por:
1.  Configurar um ambiente de teste com variáveis de ambiente 'dummy'
    para satisfazer o módulo de configurações da aplicação (`src/settings.py`)
    durante a inicialização do pytest. Isso é feito no nível do módulo, ANTES
    de qualquer importação de `src`.
2.  Configurar um banco de dados de teste isolado em memória (SQLite) para
    cada função de teste, garantindo que os testes não interfiram uns com os
    outros.
3.  Criar um cliente de teste da aplicação FastAPI (`TestClient`) com a
    dependência de banco de dados sobrescrita para usar o banco de teste.
4.  Fornecer 'payloads' de dados (dicionários) para a criação de usuários
    comuns e superusuários, incluindo todos os campos de perfil obrigatórios.
5.  Criar usuários (comum e superusuário) e gerar tokens de autenticação
    para serem usados em testes de endpoints protegidos. A fixture de criação
    de usuário é idempotente para evitar falhas em execuções repetidas.
"""

# -------------------------------------------------------------------------- #
#                 SETUP DE AMBIENTE E IMPORTS NECESSÁRIOS                    #
# -------------------------------------------------------------------------- #

import os

os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_password"
os.environ["POSTGRES_SERVER"] = "test_db_server"
os.environ["POSTGRES_PORT"] = "5433"
os.environ["POSTGRES_DB"] = "test_db_name"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_that_is_long_enough"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy_key_for_testing"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_dummy_webhook_secret_for_testing"
os.environ["CLIENT_URL"] = "http://testfrontend"
os.environ["MELHOR_ENVIO_TOKEN"] = "dummy_melhor_envio_token"
os.environ["STORE_ORIGIN_CEP"] = "01001000"


import pytest
from typing import Dict, Generator

from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src import crud, models, schemas
from src.auth import create_access_token
from src.database import Base, get_db
from src.main import app as main_app
from src.schemas import UserCreate

# -------------------------------------------------------------------------- #
#                       SETUP DO BANCO DE DADOS DE TESTE                     #
# -------------------------------------------------------------------------- #

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# -------------------------------------------------------------------------- #
#                             FIXTURES PRINCIPAIS                            #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Cria e destrói um banco de dados em memória para cada função de teste."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Cria um cliente de teste para a aplicação FastAPI, sobrescrevendo a
    dependência `get_db` para usar o banco de dados de teste em memória.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    main_app.dependency_overrides[get_db] = override_get_db

    with TestClient(main_app) as test_client:
        yield test_client

    main_app.dependency_overrides.clear()


# -------------------------------------------------------------------------- #
#                 FIXTURES DE DADOS (PAYLOADS) PARA USUÁRIOS                 #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def test_superuser_payload() -> Dict:
    """Retorna um dicionário (payload) com dados completos para criar um superusuário."""
    return {
        "email": "admin@test.com",
        "password": "password123",
        "full_name": "Admin User",
        "cpf": "655.104.190-67",
        "phone": "(11) 99999-8888",
        "address_street": "Admin Street",
        "address_number": "100",
        "address_complement": "Sala 1",
        "address_zip": "12345-001",
        "address_city": "Adminville",
        "address_state": "AD",
    }


@pytest.fixture(scope="session")
def test_user_payload() -> Dict:
    """Retorna um dicionário (payload) com dados completos para criar um usuário comum."""
    return {
        "email": "user@test.com",
        "password": "password123",
        "full_name": "Common User",
        "cpf": "021.357.920-04",
        "phone": "(22) 88888-7777",
        "address_street": "User Avenue",
        "address_number": "202",
        "address_complement": None,
        "address_zip": "54321-002",
        "address_city": "Userville",
        "address_state": "US",
    }


# -------------------------------------------------------------------------- #
#               FIXTURES DE CRIAÇÃO DE USUÁRIOS E AUTENTICAÇÃO               #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def test_superuser(db_session: Session, test_superuser_payload: Dict) -> models.User:
    """Cria um superusuário de teste diretamente no banco de dados e o retorna."""
    user_schema = UserCreate(**test_superuser_payload)
    user = crud.get_user_by_email(db_session, email=user_schema.email)
    if not user:
        user = crud.create_user(db=db_session, user=user_schema, is_superuser=True)
    return user


@pytest.fixture(scope="function")
def test_user(client: TestClient, test_user_payload: Dict, db_session: Session) -> Dict:
    """
    Garante que um usuário comum exista e retorna seus dados.

    Tenta criar o usuário via API para testar o endpoint. Se o usuário já
    existir (retorno 400), ele é buscado no banco. Isso torna a fixture
    idempotente e resiliente a múltiplas chamadas.
    """
    response = client.post("/auth/users/", json=test_user_payload)

    if response.status_code == 201:
        return response.json()

    if response.status_code == 400 and "already registered" in response.json().get(
        "detail", ""
    ):
        user = crud.get_user_by_email(db_session, email=test_user_payload["email"])
        assert user is not None
        return schemas.User.model_validate(user).model_dump()

    response.raise_for_status()
    return {}


@pytest.fixture(scope="function")
def superuser_token_headers(test_superuser: models.User) -> Dict[str, str]:
    """Gera um cabeçalho de autenticação Bearer para o superusuário de teste."""
    token = create_access_token(data={"sub": test_superuser.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user_token_headers(client: TestClient, test_user_payload: Dict) -> Dict[str, str]:
    """
    Garante que o usuário de teste exista, faz o login e gera o cabeçalho
    de autenticação para o usuário comum.
    """
    client.post("/auth/users/", json=test_user_payload)

    login_data = {
        "username": test_user_payload["email"],
        "password": test_user_payload["password"],
    }
    response = client.post("/auth/token", data=login_data)
    response.raise_for_status()

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
