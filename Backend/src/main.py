"""
Módulo principal da aplicação FastAPI.

Este arquivo serve como o ponto de entrada principal:
1. Cria a instância da aplicação FastAPI.
2. Importa e registra todos os roteadores dos diferentes recursos.
"""

# -------------------------------------------------------------------------- #
#                         IMPORTS FUNDAMENTAIS                               #
# -------------------------------------------------------------------------- #
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine, Base  # noqa: F401

# -------------------------------------------------------------------------- #
#                        IMPORTS DOS MÓDULOS DE ROTAS                        #
# -------------------------------------------------------------------------- #
from .routers import auth
from .routers import cart
from .routers import categories
from .routers import coupons
from .routers import orders
from .routers import payments
from .routers import products
from .routers import reviews
from .routers import users
from .routers import shipping
from .routers import general_stats 
from .routers.dashboard import financial_reports


# -------------------------------------------------------------------------- #
#                        LIFESPAN E INICIALIZAÇÃO DO DB                      #
# -------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para o ciclo de vida da aplicação.
    Garante que as tabelas do banco de dados sejam criadas na inicialização.
    """
    yield


# -------------------------------------------------------------------------- #
#                  CRIAÇÃO E CONFIGURAÇÃO DA APLICAÇÃO E CORS                #
# -------------------------------------------------------------------------- #
app = FastAPI(
    title="E-Commerce",
    version="1.0.0",
    description="Seu E-Commerce.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------- #
#                         INCLUSÃO DOS ROTEADORES                            #
# -------------------------------------------------------------------------- #
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(coupons.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(users.router)
app.include_router(shipping.router)
app.include_router(general_stats.router)
app.include_router(financial_reports.router)


# -------------------------------------------------------------------------- #
#                                 ROOT ENDPOINT                              #
# -------------------------------------------------------------------------- #
@app.get("/", tags=["Root"])
def read_root():
    """Endpoint raiz para verificar se a API está online."""
    return {"message": "API do E-commerce está online."}
