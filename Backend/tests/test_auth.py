"""
Suíte de Testes para os recursos de Autenticação e Usuários.

Testa os endpoints de registro, login, perfil, atualização de perfil e
alteração de senha. Garante que:
1.  O registro de um novo usuário só é bem-sucedido com dados completos
    (perfil e endereço) e um CPF válido.
2.  O login funciona corretamente e retorna um token JWT.
3.  O endpoint de perfil de usuário (`/users/me`) retorna os dados corretos
    do usuário autenticado.
4.  Um usuário autenticado pode atualizar seus dados cadastrais.
5.  Um usuário autenticado pode alterar sua senha fornecendo a senha antiga.
6.  Casos de borda de autenticação e validação são tratados adequadamente.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import Dict

from fastapi.testclient import TestClient

from src.auth import create_access_token

# -------------------------------------------------------------------------- #
#                       TESTES DE REGISTRO DE USUÁRIO                        #
# -------------------------------------------------------------------------- #


def test_create_user_success(client: TestClient, test_user_payload: Dict):
    """Testa o registro bem-sucedido de um novo usuário com dados completos."""
    payload = test_user_payload.copy()
    payload["email"] = "register_success@test.com"
    payload["cpf"] = "53043260082"

    response = client.post("/auth/users/", json=payload)
    assert response.status_code == 201, response.text

    created_user = response.json()
    assert created_user["email"] == payload["email"]
    assert "password" not in created_user
    assert not created_user["is_superuser"]


def test_create_user_with_missing_field_fails(
    client: TestClient, test_user_payload: Dict
):
    """Testa a falha de registro ao omitir um campo obrigatório (ex: full_name)."""
    payload = test_user_payload.copy()
    payload.pop("full_name")

    response = client.post("/auth/users/", json=payload)
    assert response.status_code == 422


def test_create_user_with_existing_email(
    client: TestClient, test_user: Dict, test_user_payload: Dict
):
    """Testa a falha ao registrar um usuário com um e-mail que já existe."""
    response = client.post("/auth/users/", json=test_user_payload)
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Email already registered"


# -------------------------------------------------------------------------- #
#                                 TESTES DE LOGIN                            #
# -------------------------------------------------------------------------- #


def test_login_for_access_token_success(
    client: TestClient, test_user: Dict, test_user_payload: Dict
):
    """Testa o login bem-sucedido com credenciais corretas."""
    login_data = {
        "username": test_user_payload["email"],
        "password": test_user_payload["password"],
    }
    response = client.post("/auth/token", data=login_data)

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_with_wrong_password(client: TestClient, test_user: Dict):
    """Testa a falha de login ao fornecer a senha incorreta."""
    login_data = {"username": test_user["email"], "password": "wrongpassword"}
    response = client.post("/auth/token", data=login_data)

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#             TESTES DE PERFIL, ATUALIZAÇÃO E ALTERAÇÃO DE SENHA             #
# -------------------------------------------------------------------------- #


def test_read_users_me_success(
    client: TestClient, user_token_headers: Dict, test_user: Dict
):
    """Testa se um usuário autenticado pode acessar seus próprios dados."""
    response = client.get("/auth/users/me/", headers=user_token_headers)
    assert response.status_code == 200

    profile_data = response.json()
    assert profile_data["email"] == test_user["email"]
    assert profile_data["id"] == test_user["id"]
    assert profile_data["full_name"] == test_user["full_name"]


def test_update_user_me_success(client: TestClient, user_token_headers: Dict):
    """Testa se um usuário autenticado pode atualizar seus dados de perfil."""
    update_payload = {
        "full_name": "New Updated Name",
        "address_street": "New Updated Street",
        "phone": "(99) 99999-9999",
    }
    response = client.put(
        "/auth/users/me/", headers=user_token_headers, json=update_payload
    )

    assert response.status_code == 200, response.text
    updated_user = response.json()
    assert updated_user["full_name"] == update_payload["full_name"]
    assert updated_user["address_street"] == update_payload["address_street"]
    assert updated_user["phone"] == update_payload["phone"]


def test_update_user_me_unauthenticated(client: TestClient):
    """Testa a falha ao tentar atualizar o perfil sem autenticação."""
    response = client.put("/auth/users/me/", json={"full_name": "Fail Name"})
    assert response.status_code == 401


def test_update_password_success_and_relogin(
    client: TestClient,
    test_user: Dict,
    user_token_headers: Dict,
    test_user_payload: Dict,
):
    """
    Testa a atualização bem-sucedida de senha e verifica se o login
    com a nova senha funciona e com a antiga falha.
    """
    new_password = "a_very_new_password"
    password_payload = {
        "current_password": test_user_payload["password"],
        "new_password": new_password,
    }
    response = client.put(
        "/auth/users/me/password", headers=user_token_headers, json=password_payload
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Password updated successfully."}

    old_login_resp = client.post(
        "/auth/token",
        data={
            "username": test_user["email"],
            "password": test_user_payload["password"],
        },
    )
    assert old_login_resp.status_code == 401

    new_login_resp = client.post(
        "/auth/token",
        data={"username": test_user["email"], "password": new_password},
    )
    assert new_login_resp.status_code == 200
    assert "access_token" in new_login_resp.json()


def test_update_password_with_wrong_current_password(
    client: TestClient, user_token_headers: Dict
):
    """Testa a falha ao tentar atualizar a senha fornecendo a senha atual incorreta."""
    password_payload = {
        "current_password": "this_is_wrong_password",
        "new_password": "it_doesnt_matter",
    }
    response = client.put(
        "/auth/users/me/password", headers=user_token_headers, json=password_payload
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect current password."


# -------------------------------------------------------------------------- #
#                       TESTES DE CASOS DE BORDA DE TOKEN                    #
# -------------------------------------------------------------------------- #


def test_read_users_me_with_invalid_token_format(client: TestClient):
    """Testa o acesso com um token Bearer malformado."""
    headers = {"Authorization": "Bearer not-a-valid-jwt"}
    response = client.get("/auth/users/me/", headers=headers)
    assert response.status_code == 401


def test_get_current_user_with_token_missing_sub(client: TestClient):
    """Testa a falha com um token JWT válido, mas sem o campo 'sub'."""
    token = create_access_token(data={"user_id": 123})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/users/me/", headers=headers)
    assert response.status_code == 401, response.text
    assert "Could not validate credentials" in response.json()["detail"]


def test_get_current_user_with_nonexistent_user_in_db(client: TestClient):
    """
    Testa a falha com um token JWT válido para um usuário que não existe
    (ou foi deletado) do banco de dados.
    """
    token = create_access_token(data={"sub": "ghost.user@example.com"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/users/me/", headers=headers)
    assert response.status_code == 401, response.text
    assert "Could not validate credentials" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                        TESTE DE VALIDAÇÃO DE DADOS                         #
# -------------------------------------------------------------------------- #


def test_create_user_with_invalid_cpf(client: TestClient, test_user_payload: Dict):
    """Testa a falha ao registrar um usuário com um CPF matematicamente inválido."""
    payload = test_user_payload.copy()
    payload["email"] = "invalid.cpf@test.com"
    payload["cpf"] = "111.111.111-11"

    response = client.post("/auth/users/", json=payload)

    assert response.status_code == 422, response.text

    error_detail = response.json()["detail"][0]
    assert "CPF fornecido é inválido" in error_detail["msg"]
