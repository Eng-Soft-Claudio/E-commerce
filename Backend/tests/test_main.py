"""
Suíte de Testes para o Módulo Principal da Aplicação.

Este arquivo contém testes básicos para o ponto de entrada da API,
verificando sua disponibilidade e resposta padrão.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from fastapi.testclient import TestClient
from src.main import app

# -------------------------------------------------------------------------- #
#                       SETUP DO CLIENTE DE TESTE                            #
# -------------------------------------------------------------------------- #
client = TestClient(app)


# -------------------------------------------------------------------------- #
#                            TESTES DO ENDPOINT RAIZ                         #
# -------------------------------------------------------------------------- #
def test_read_main():
    """
    Testa se o endpoint raiz ("/") está respondendo corretamente.

    Verifica se:
    1. O status code da resposta é 200 (OK).
    2. O corpo da resposta contém a mensagem de boas-vindas esperada.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API do E-commerce está online."}
