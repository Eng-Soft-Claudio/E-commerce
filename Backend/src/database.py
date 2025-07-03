"""
Módulo de Banco de Dados.

Esta implementação conecta a aplicação ao banco de dados PostgreSQL
configurado através das variáveis de ambiente e fornece a dependência
`get_db` para gerenciar as sessões em cada requisição.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .settings import settings

# -------------------------------------------------------------------------- #
#                       CONFIGURAÇÃO INICIAL E LOGGING                       #
# -------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# -------------------------------------------------------------------------- #
#                         CONFIGURAÇÃO DO BANCO DE DADOS                     #
# -------------------------------------------------------------------------- #

engine = create_engine(str(settings.DATABASE_URL))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# -------------------------------------------------------------------------- #
#                         DEPENDÊNCIA GET_DB                                 #
# -------------------------------------------------------------------------- #


def get_db():
    """
    Dependência do FastAPI que cria e gerencia uma sessão de DB por requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
