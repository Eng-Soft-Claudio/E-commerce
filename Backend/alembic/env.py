"""
Script de configuração de ambiente para o Alembic.

Este arquivo é o ponto de entrada que o Alembic utiliza para configurar o
contexto de migração. É responsável por duas tarefas principais:

1.  Carregar a URL de conexão do banco de dados a partir das configurações
    centrais da aplicação (`src/settings.py`), garantindo uma única fonte de
    verdade para a conexão com o banco de dados.

2.  Carregar o metadado (`Base.metadata`) dos modelos SQLAlchemy do projeto,
    permitindo que o Alembic detecte automaticamente as alterações no schema
    ao usar o comando 'autogenerate'.

Para que as importações de 'src' funcionem, o caminho raiz do projeto
é temporariamente adicionado ao `sys.path`.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# -------------------------------------------------------------------------- #
#                     SETUP DE CAMINHOS E AMBIENTE                           #
# -------------------------------------------------------------------------- #

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import Base  # noqa: E402
from src.models import *  # noqa: F401, F403, E402
from src.settings import settings  # noqa: E402

# -------------------------------------------------------------------------- #
#                         CONFIGURAÇÃO GERAL DO ALEMBIC                      #
# -------------------------------------------------------------------------- #

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

target_metadata = Base.metadata

# -------------------------------------------------------------------------- #
#                      FUNÇÕES DE EXECUÇÃO DA MIGRAÇÃO                       #
# -------------------------------------------------------------------------- #


def run_migrations_offline() -> None:
    """Executa migrações no modo 'offline'.

    Este modo configura o contexto apenas com uma URL de banco de dados, sem
    estabelecer uma conexão real. Ele é usado para gerar scripts SQL que podem
    ser inspecionados ou executados manualmente.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações no modo 'online'.

    Neste modo, um Engine SQLAlchemy é criado e uma conexão com o banco
    de dados é estabelecida. As migrações são executadas diretamente
    contra o banco de dados.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# -------------------------------------------------------------------------- #
#                        BLOCO DE EXECUÇÃO PRINCIPAL                         #
# -------------------------------------------------------------------------- #

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()