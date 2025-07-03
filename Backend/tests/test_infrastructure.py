"""
Suíte de Testes para a Infraestrutura da Aplicação.

Testa componentes de baixo nível como as dependências de banco de dados,
garantindo que o ciclo de vida da sessão (abertura e fechamento) funcione
como esperado fora do ambiente de teste com 'overrides'.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database import get_db, Base
from conftest import engine as test_engine

# -------------------------------------------------------------------------- #
#                       SETUP DA APLICAÇÃO E ENDPOINT DE TESTE               #
# -------------------------------------------------------------------------- #

app_for_db_test = FastAPI()


@app_for_db_test.get("/test-db")
def db_dependency_test_endpoint(db: Session = Depends(get_db)):
    """
    Este endpoint simples existe apenas para usar a dependência 'get_db' real.
    Verifica se a sessão recebida está ativa.
    """
    assert db.is_active
    return {"status": "success"}


# -------------------------------------------------------------------------- #
#                          TESTE DA DEPENDÊNCIA GET_DB                       #
# -------------------------------------------------------------------------- #


def test_get_db_dependency_lifecycle(monkeypatch: pytest.MonkeyPatch):
    """
    Testa se a dependência `get_db` original cria, fornece e fecha uma sessão.

    Este teste usa a fixture `monkeypatch` do Pytest para substituir
    dinamicamente a `engine` do PostgreSQL no módulo `src.database` pela
    nossa `test_engine` do SQLite em memória. Isso faz com que a função `get_db`
    original opere sobre o banco de dados de teste, permitindo-nos verificar
    seu ciclo de vida (criação, yield, fechamento) sem tentar se conectar
    a um servidor de banco de dados externo.
    """
    monkeypatch.setattr("src.database.engine", test_engine)
    monkeypatch.setattr("src.database.SessionLocal.kw", {"bind": test_engine})

    Base.metadata.create_all(bind=test_engine)

    with TestClient(app_for_db_test) as client:
        response = client.get("/test-db")
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

    Base.metadata.drop_all(bind=test_engine)
