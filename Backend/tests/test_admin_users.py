"""
Suíte de Testes para Gerenciamento de Usuários pelo Administrador.

Testa todos os endpoints sob o prefixo `/admin/users`, garantindo que:
1.  Um administrador (superuser) pode listar todos os usuários.
2.  Um administrador pode buscar um usuário específico pelo seu ID.
3.  Um administrador pode atualizar os dados de um usuário, incluindo seu
    status de ativação (`is_active`) e de superusuário (`is_superuser`).
4.  A atualização falha apropriadamente para usuários inexistentes.
5.  Um administrador não pode deletar a si mesmo.
6.  Um administrador pode deletar permanentemente outro usuário.
7.  A deleção falha apropriadamente para usuários inexistentes.
8.  Um usuário comum não tem acesso a nenhum desses endpoints.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

import pytest
from typing import Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models

# -------------------------------------------------------------------------- #
#                             FIXTURE AUXILIAR                             #
# -------------------------------------------------------------------------- #


@pytest.fixture
def user_for_admin_management(
    client: TestClient, test_user_payload: Dict
) -> Dict[str, Any]:
    """
    Cria um usuário comum, garantindo que ele exista para ser gerenciado
    nos testes. Usa um e-mail diferente para evitar colisões com fixtures
    de `conftest`. Retorna o dicionário completo do usuário criado.
    """
    payload = test_user_payload.copy()
    payload["email"] = "manage.me@test.com"
    payload["cpf"] = "32517495017"  

    response = client.post("/auth/users/", json=payload)
    response.raise_for_status()
    return response.json()


# -------------------------------------------------------------------------- #
#                       TESTES DE CONTROLE DE ACESSO                         #
# -------------------------------------------------------------------------- #


def test_common_user_cannot_access_admin_user_routes(
    client: TestClient, user_token_headers: Dict, user_for_admin_management: Dict
):
    """
    Verifica se um usuário comum recebe erro 403 (Forbidden) ao tentar
    acessar qualquer rota de gerenciamento de usuários.
    """
    user_id = user_for_admin_management["id"]
    get_all_response = client.get("/admin/users/", headers=user_token_headers)
    get_one_response = client.get(f"/admin/users/{user_id}", headers=user_token_headers)
    update_response = client.put(
        f"/admin/users/{user_id}",
        headers=user_token_headers,
        json={"is_active": False},
    )
    delete_response = client.delete(
        f"/admin/users/{user_id}", headers=user_token_headers
    )

    assert get_all_response.status_code == 403
    assert get_one_response.status_code == 403
    assert update_response.status_code == 403
    assert delete_response.status_code == 403


# -------------------------------------------------------------------------- #
#                      TESTES DE LEITURA (GET) DE USUÁRIOS                   #
# -------------------------------------------------------------------------- #


def test_admin_can_list_all_users(
    client: TestClient, superuser_token_headers: Dict, user_for_admin_management: Dict
):
    """
    Testa se um superusuário pode listar todos os usuários (clientes), e
    se o usuário recém-criado está presente na lista.
    """
    response = client.get("/admin/users/", headers=superuser_token_headers)
    assert response.status_code == 200, response.text
    user_list = response.json()
    assert isinstance(user_list, list)
    assert any(user["id"] == user_for_admin_management["id"] for user in user_list), (
        "O usuário de teste não foi encontrado na lista"
    )


def test_admin_can_get_user_by_id(
    client: TestClient, superuser_token_headers: Dict, user_for_admin_management: Dict
):
    """
    Testa se um superusuário pode buscar os dados de um usuário
    específico pelo seu ID.
    """
    user_id = user_for_admin_management["id"]
    response = client.get(f"/admin/users/{user_id}", headers=superuser_token_headers)

    assert response.status_code == 200, response.text
    user_data = response.json()
    assert user_data["id"] == user_id
    assert user_data["email"] == user_for_admin_management["email"]


def test_admin_get_nonexistent_user_by_id(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao buscar um usuário com ID inexistente."""
    response = client.get("/admin/users/99999", headers=superuser_token_headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                       TESTES DE ATUALIZAÇÃO (PUT)                          #
# -------------------------------------------------------------------------- #


def test_admin_can_update_user(
    client: TestClient,
    superuser_token_headers: Dict,
    user_for_admin_management: Dict,
    db_session: Session,
):
    """
    Testa se o superusuário pode atualizar os dados de um usuário,
    incluindo a desativação da conta e a promoção para superusuário.
    """
    user_id = user_for_admin_management["id"]
    update_payload = {
        "full_name": "Nome Atualizado Pelo Admin",
        "is_active": False,
        "is_superuser": True,
    }

    response = client.put(
        f"/admin/users/{user_id}",
        headers=superuser_token_headers,
        json=update_payload,
    )
    assert response.status_code == 200, response.text

    db_session.expire_all()
    user_in_db = db_session.get(models.User, user_id)
    assert user_in_db is not None
    assert user_in_db.full_name == update_payload["full_name"]
    assert user_in_db.is_active is False
    assert user_in_db.is_superuser is True


def test_admin_update_nonexistent_user(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao tentar atualizar um usuário com ID inexistente."""
    response = client.put(
        "/admin/users/99999",
        headers=superuser_token_headers,
        json={"is_active": True},
    )
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                        TESTES DE DELEÇÃO (DELETE)                          #
# -------------------------------------------------------------------------- #


def test_admin_can_delete_user(
    client: TestClient,
    superuser_token_headers: Dict,
    user_for_admin_management: Dict,
    db_session: Session,
):
    """Testa se o superusuário pode deletar permanentemente outro usuário."""
    user_id = user_for_admin_management["id"]
    response = client.delete(f"/admin/users/{user_id}", headers=superuser_token_headers)

    assert response.status_code == 200
    assert response.json() == {"message": "User deleted successfully."}

    db_session.expire_all()
    user_in_db = db_session.get(models.User, user_id)
    assert user_in_db is None


def test_admin_cannot_delete_self(
    client: TestClient, superuser_token_headers: Dict, test_superuser: models.User
):
    """Testa se um superusuário é impedido de deletar a própria conta."""
    superuser_id = test_superuser.id
    response = client.delete(
        f"/admin/users/{superuser_id}", headers=superuser_token_headers
    )
    assert response.status_code == 400
    assert "cannot delete your own account" in response.json()["detail"]


def test_admin_delete_nonexistent_user(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao tentar deletar um usuário com ID inexistente."""
    response = client.delete("/admin/users/99999", headers=superuser_token_headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
