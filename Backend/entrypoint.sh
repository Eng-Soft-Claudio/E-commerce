#!/bin/bash
# ========================================================================== #
#                     SCRIPT DE ENTRYPOINT PARA A API                        #
# ========================================================================== #
# Este script orquestra a inicialização do contêiner da API, garantindo que
# o banco de dados esteja acessível e com as migrações mais recentes
# aplicadas antes de iniciar o servidor da aplicação.

# -------------------------------------------------------------------------- #
#                         ESPERAR O BANCO DE DADOS                           #
# -------------------------------------------------------------------------- #
echo "Aguardando o banco de dados iniciar..."
while ! nc -z $POSTGRES_SERVER $POSTGRES_PORT; do
  sleep 1
done
echo "Banco de dados iniciado com sucesso."

# -------------------------------------------------------------------------- #
#                          APLICAR MIGRAÇÕES                                 #
# -------------------------------------------------------------------------- #
echo "Aplicando migrações do banco de dados..."
alembic upgrade head
echo "Migrações aplicadas com sucesso."

# -------------------------------------------------------------------------- #
#                           INICIAR A APLICAÇÃO                              #
# -------------------------------------------------------------------------- #
echo "Iniciando a aplicação FastAPI..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --proxy-headers --forwarded-allow-ips '*'