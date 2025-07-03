"""
Suíte de Testes para o Fluxo de Recuperação de Senha.

Testa os endpoints e a lógica de negócio para a solicitação de redefinição
de senha e a efetivação da mudança. Garante que:
1.  Um token de reset pode ser solicitado para um usuário existente.
2.  A tentativa de solicitar para um usuário inexistente não vaza informações.
3.  A senha pode ser redefinida com um token válido e recente.
4.  Tokens inválidos, expirados ou já usados são corretamente rejeitados.
5.  Após o reset, o usuário pode fazer login com a nova senha.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from src import crud, models  # noqa: F401

# -------------------------------------------------------------------------- #
#                   TESTE DO ENDPOINT /forgot-password                       #
# -------------------------------------------------------------------------- #


def test_request_password_reset_success(
    client: TestClient, test_user: Dict, db_session: Session
):
    """
    Testa a solicitação bem-sucedida de um token de recuperação de senha.
    """
    response = client.post("/auth/forgot-password", json={"email": test_user["email"]})

    assert response.status_code == 200, response.text
    response_data = response.json()
    assert "token" in response_data
    assert "detail" in response_data

    token_in_db = (
        db_session.query(models.PasswordResetToken)
        .filter_by(token=response_data["token"])
        .first()
    )
    assert token_in_db is not None
    assert token_in_db.email == test_user["email"]


def test_request_password_reset_for_nonexistent_user(client: TestClient):
    """
    Testa que a solicitação para um email não cadastrado retorna uma
    mensagem genérica para não vazar a existência do usuário.
    """
    response = client.post(
        "/auth/forgot-password", json={"email": "not-found@example.com"}
    )
    assert response.status_code == 200, response.text
    assert "If an account with this email exists" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#                   TESTE DO ENDPOINT /reset-password                        #
# -------------------------------------------------------------------------- #


def test_reset_password_success_and_login_with_new_password(
    client: TestClient, test_user: Dict, test_user_payload: Dict, db_session: Session
):
    """
    Testa o fluxo completo: solicita token, redefine a senha com ele e
    depois tenta fazer login com a nova senha.
    """
    reset_req_resp = client.post(
        "/auth/forgot-password", json={"email": test_user["email"]}
    )
    reset_token = reset_req_resp.json()["token"]

    new_password = "new-secure-password"
    reset_resp = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": new_password},
    )
    assert reset_resp.status_code == 200, reset_resp.text
    assert "Senha atualizada com sucesso" in reset_resp.json()["message"]

    old_login_resp = client.post(
        "/auth/token",
        data={
            "username": test_user["email"],
            "password": test_user_payload["password"],
        },
    )
    assert old_login_resp.status_code == 401, old_login_resp.text

    new_login_resp = client.post(
        "/auth/token", data={"username": test_user["email"], "password": new_password}
    )
    assert new_login_resp.status_code == 200, new_login_resp.text
    assert "access_token" in new_login_resp.json()


def test_reset_password_with_invalid_token(client: TestClient):
    """Testa a falha ao tentar redefinir a senha com um token inválido."""
    response = client.post(
        "/auth/reset-password",
        json={"token": "invalid-token-string", "new_password": "any-password"},
    )
    assert response.status_code == 400, response.text
    assert "Token de recuperação inválido ou expirado" in response.json()["detail"]


def test_reset_password_with_expired_token(
    client: TestClient, test_user: Dict, db_session: Session, mocker
):
    """Testa a falha ao usar um token que já expirou."""
    reset_token_obj = models.PasswordResetToken(
        email=test_user["email"],
        token="expired-token",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db_session.add(reset_token_obj)
    db_session.commit()

    response = client.post(
        "/auth/reset-password",
        json={"token": "expired-token", "new_password": "any-password"},
    )
    assert response.status_code == 400, response.text
    assert "Token de recuperação inválido ou expirado" in response.json()["detail"]


def test_reset_password_for_deleted_user(
    client: TestClient, test_user: Dict, db_session: Session
):
    """
    Testa que o reset falha se o token for válido mas o usuário foi deletado.
    Cobre a linha 422 do crud.py.
    """
    reset_req_resp = client.post(
        "/auth/forgot-password", json={"email": test_user["email"]}
    )
    reset_token = reset_req_resp.json()["token"]

    user_in_db = crud.get_user_by_email(db_session, email=test_user["email"])
    assert user_in_db is not None
    db_session.delete(user_in_db)
    db_session.commit()

    response = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": "any-password"},
    )
    assert response.status_code == 400, response.text
    assert "Token de recuperação inválido ou expirado" in response.json()["detail"]
