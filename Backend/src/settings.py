"""
Módulo para gerenciar configurações da aplicação a partir de variáveis de ambiente.

Esta implementação usa pathlib para construir um caminho absoluto para o arquivo .env,
resolvendo problemas de análise estática e garantindo que o arquivo seja
encontrado independentemente do diretório de trabalho atual.

Para interoperabilidade com o Pytest, o módulo detecta se está sendo executado
no contexto de teste (`"pytest" in sys.modules`). Se estiver, ele ignora a
leitura do arquivo .env e depende exclusivamente das variáveis de ambiente,
que são fornecidas pelo `conftest.py`.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
import sys
from pathlib import Path
from typing import Dict, Any, Optional  # noqa: F401
from pydantic import Field, PostgresDsn, computed_field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# -------------------------------------------------------------------------- #
#                         CONFIGURAÇÃO DE CAMINHOS                           #
# -------------------------------------------------------------------------- #
ROOT_DIR = Path(__file__).parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"

# -------------------------------------------------------------------------- #
#                          CLASSE DE CONFIGURAÇÕES                           #
# -------------------------------------------------------------------------- #


class Settings(BaseSettings):
    """
    Carrega as configurações a partir do .env, do ambiente ou de ambos.
    Valida a presença de chaves essenciais para o funcionamento da aplicação.
    """

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    JWT_SECRET_KEY: str = Field(...)

    STRIPE_SECRET_KEY: str = Field(...)
    STRIPE_WEBHOOK_SECRET: str = Field(...)
    CLIENT_URL: str = "http://localhost:3000"

    MELHOR_ENVIO_TOKEN: str = Field(...)
    STORE_ORIGIN_CEP: str = Field(..., pattern=r"^\d{8}$")

    _config_dict: Dict[str, Any] = {"env_file_encoding": "utf-8", "extra": "ignore"}

    if "pytest" not in sys.modules:
        _config_dict["env_file"] = str(ENV_FILE_PATH)

    model_config = SettingsConfigDict(**_config_dict)


# -------------------------------------------------------------------------- #
#           FUNÇÃO DE INICIALIZAÇÃO E EXPORTAÇÃO DAS CONFIGURAÇÕES           #
# -------------------------------------------------------------------------- #


def load_settings() -> Settings:
    """
    Carrega e valida as configurações. Levanta um erro em caso de falha.
    """
    try:
        return Settings.model_validate({})
    except ValidationError as e:
        raise RuntimeError(
            "Verifique se o arquivo .env existe e contém as variáveis necessárias, "
            "ou se as variáveis de ambiente estão configuradas corretamente para o teste."
        ) from e


settings = load_settings()
