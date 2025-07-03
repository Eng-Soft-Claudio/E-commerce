# ========================================================================== #
#                    DOCKERFILE PARA APLICAÇÃO FASTAPI                       #
# ========================================================================== #
# Este Dockerfile define os passos para criar uma imagem Docker para a
# aplicação FastAPI. Ele configura um ambiente Python, instala as
# dependências, copia o código fonte e define o comando de inicialização
# através de um script entrypoint.

# -------------------------------------------------------------------------- #
#                                IMAGEM BASE                                 #
# -------------------------------------------------------------------------- #
# Utiliza uma imagem oficial do Python como base. A tag "slim" oferece um
# bom equilíbrio entre tamanho reduzido e a disponibilidade das bibliotecas
# de sistema essenciais.
FROM python:3.13-slim

# -------------------------------------------------------------------------- #
#                         DIRETÓRIO DE TRABALHO                              #
# -------------------------------------------------------------------------- #
# Define o diretório de trabalho padrão dentro do contêiner. Todos os
# comandos subsequentes (RUN, COPY, CMD) serão executados a partir deste
# caminho.
WORKDIR /app

# -------------------------------------------------------------------------- #
#                 INSTALAÇÃO DE DEPENDÊNCIAS DE SISTEMA                      #
# -------------------------------------------------------------------------- #
# Instala pacotes do sistema operacional necessários, como o cliente do
# PostgreSQL e o netcat (para o healthcheck no entrypoint).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        netcat-openbsd \
        git \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------------------- #
#                   INSTALAÇÃO DE DEPENDÊNCIAS PYTHON                        #
# -------------------------------------------------------------------------- #
# Copia o arquivo de dependências separadamente para aproveitar o cache de
# camadas do Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------------------- #
#                   CÓPIA DO CÓDIGO FONTE E ENTRYPOINT                       #
# -------------------------------------------------------------------------- #
# Copia o código fonte e o script de inicialização para dentro do contêiner.
COPY ./src ./src
COPY ./alembic ./alembic
COPY alembic.ini .
COPY entrypoint.sh .

# Torna o script entrypoint executável
RUN chmod +x /app/entrypoint.sh

# -------------------------------------------------------------------------- #
#                      CONFIGURAÇÃO DE REDE E EXECUÇÃO                       #
# -------------------------------------------------------------------------- #
# Expõe a porta em que a aplicação será executada.
EXPOSE 8000

# Define o script de entrypoint que será executado ao iniciar o contêiner.
ENTRYPOINT ["/app/entrypoint.sh"]