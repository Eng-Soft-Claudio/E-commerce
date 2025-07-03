"""
Define os modelos do SQLAlchemy ORM.

Cada classe aqui representa uma tabela no banco de dados e define seus campos,
tipos e relacionamentos. Este módulo é a única fonte de verdade para a
estrutura do schema do banco de dados, sendo utilizado pelo Alembic para gerar
scripts de migração e pela aplicação para interagir com os dados.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, Optional

from .database import Base

# -------------------------------------------------------------------------- #
#                               MODELO DE CATEGORIA                          #
# -------------------------------------------------------------------------- #


class Category(Base):
    """
    Modelo SQLAlchemy representando a tabela 'categories' no banco de dados.
    Armazena categorias que agrupam diferentes produtos.
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    products: Mapped[List["Product"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


# -------------------------------------------------------------------------- #
#                                MODELO DE PRODUTO                           #
# -------------------------------------------------------------------------- #


class Product(Base):
    """
    Modelo SQLAlchemy representando a tabela 'products' no banco de dados.
    Contém todos os detalhes de um produto, incluindo estoque, preço e dados
    logísticos (peso e dimensões) essenciais para o cálculo de frete.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, index=True)
    image_url: Mapped[Optional[str]]
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    stock: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    # Campos de Logística para Cálculo de Frete
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    height_cm: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    width_cm: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    length_cm: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")

    category: Mapped["Category"] = relationship(back_populates="products")
    reviews: Mapped[List["ProductReview"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


# -------------------------------------------------------------------------- #
#                                MODELO DE USUÁRIO                           #
# -------------------------------------------------------------------------- #


class User(Base):
    """
    Modelo SQLAlchemy representando a tabela 'users' no banco de dados.
    Armazena dados de autenticação e informações pessoais de clientes e admins,
    com todos os campos de perfil sendo obrigatórios para garantir rastreabilidade.
    Inclui um status `is_active` para desativação lógica de contas.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default="true"
    )

    full_name: Mapped[str] = mapped_column(String)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(15))
    address_street: Mapped[str] = mapped_column(String)
    address_number: Mapped[str] = mapped_column(String)
    address_complement: Mapped[str | None] = mapped_column(String, nullable=True)
    address_zip: Mapped[str] = mapped_column(String(9))
    address_city: Mapped[str] = mapped_column(String)
    address_state: Mapped[str] = mapped_column(String(2))

    cart: Mapped["Cart"] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(back_populates="customer")
    reviews: Mapped[List["ProductReview"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


# -------------------------------------------------------------------------- #
#                         MODELOS DE CARRINHO DE COMPRAS                     #
# -------------------------------------------------------------------------- #


class Cart(Base):
    """
    Modelo para o carrinho de compras, ligado um-para-um com um usuário.
    Atua como um contêiner para os itens que o usuário pretende comprar.
    Pode ter um cupom de desconto associado.
    """

    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    coupon_id: Mapped[Optional[int]] = mapped_column(ForeignKey("coupons.id"))

    owner: Mapped["User"] = relationship(back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )
    coupon: Mapped[Optional["Coupon"]] = relationship()


class CartItem(Base):
    """
    Modelo para um item dentro de um carrinho de compras.
    Associa um produto e uma quantidade a um carrinho específico.
    """

    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


# -------------------------------------------------------------------------- #
#                           MODELOS DE PEDIDO                                #
# -------------------------------------------------------------------------- #


class Order(Base):
    """
    Modelo para um pedido, representando uma compra.
    Contém o snapshot de uma transação, incluindo preço total, desconto
    aplicado e status.
    """

    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    total_price: Mapped[float] = mapped_column(Float)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    coupon_code_used: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending_payment")
    payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True
    )

    customer: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(cascade="all, delete-orphan")


class OrderItem(Base):
    """
    Modelo para um item individual dentro de um pedido.
    Armazena a quantidade e o preço de um produto no momento da compra.
    """

    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer)
    price_at_purchase: Mapped[float] = mapped_column(Float)

    product: Mapped[Optional["Product"]] = relationship()


# -------------------------------------------------------------------------- #
#                     MODELO DE AVALIAÇÃO DE PRODUTO                         #
# -------------------------------------------------------------------------- #


class ProductReview(Base):
    """
    Modelo para armazenar la avaliação (review) de um produto por um usuário.
    Cada usuário pode avaliar um produto apenas uma vez.
    """

    __tablename__ = "product_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="reviews")
    author: Mapped["User"] = relationship(back_populates="reviews")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_review"),
    )


# -------------------------------------------------------------------------- #
#                        MODELO DE CUPOM DE DESCONTO                         #
# -------------------------------------------------------------------------- #


class Coupon(Base):
    """
    Modelo para armazenar cupons de desconto.
    """

    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# -------------------------------------------------------------------------- #
#                        MODELO DE RECUPERAÇÃO DE SENHA                      #
# -------------------------------------------------------------------------- #


class PasswordResetToken(Base):
    """
    Modelo para armazenar tokens de recuperação de senha.

    Cada token é associado a um email, tem um tempo de vida limitado e
    só pode ser usado uma vez, garantindo a segurança do processo de
    recuperação de conta.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, index=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("email", "token"),)
