"""
Suíte de Testes para o módulo de Configurações (Settings).
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
import pytest
from pydantic import ValidationError
from src.settings import load_settings

# -------------------------------------------------------------------------- #
#                           TESTES DE CONFIGURAÇÃO                           #
# -------------------------------------------------------------------------- #


def test_load_settings_successfully():
    """
    Testa o caminho feliz, onde a função load_settings retorna
    as configurações com sucesso a partir do arquivo .env.
    """
    loaded_settings = load_settings()
    assert loaded_settings.STRIPE_SECRET_KEY.startswith("sk_test")
    assert loaded_settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_")


def test_load_settings_fails_on_validation_error(mocker):
    """
    Testa o caminho de falha, onde a validação Pydantic falha.
    O mock intercepta o método `model_validate` para simular o erro,
    o que força a execução do nosso bloco 'except'.
    """
    mocker.patch(
        "src.settings.Settings.model_validate",
        side_effect=ValidationError.from_exception_data(
            "Erro de validação simulado", []
        ),
    )

    with pytest.raises(RuntimeError) as excinfo:
        load_settings()

    assert "Verifique se o arquivo .env existe" in str(excinfo.value)
