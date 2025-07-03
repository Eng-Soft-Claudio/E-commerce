"""
Define os schemas Pydantic para validação de dados da API.

Este módulo estabelece os "contratos" de dados para a aplicação. Todos os
schemas de criação (ex: UserCreate, ProductCreate) definem os dados de
entrada obrigatórios, enquanto os schemas de leitura (ex: User, Product)
definem a estrutura dos dados de saída. A biblioteca 'validate_docbr' é
utilizada para garantir a validade de documentos como o CPF.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)
from validate_docbr import CPF

# -------------------------------------------------------------------------- #
#                       SCHEMAS DE CUPOM DE DESCONTO                         #
# -------------------------------------------------------------------------- #


class CouponBase(BaseModel):
    """Schema base para um cupom de desconto."""

    code: str = Field(..., max_length=20)
    discount_percent: float = Field(..., gt=0, le=100)
    expires_at: Optional[datetime] = None
    is_active: bool = True


class CouponCreate(CouponBase):
    """Schema para a criação de um novo cupom."""

    pass


class CouponUpdate(BaseModel):
    """Schema para atualização parcial de um cupom."""

    code: Optional[str] = Field(None, max_length=20)
    discount_percent: Optional[float] = Field(None, gt=0, le=100)
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class Coupon(CouponBase):
    """Schema completo para a leitura de um cupom."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class ApplyCouponRequest(BaseModel):
    """Schema para o corpo da requisição de aplicação de cupom."""

    code: str


# -------------------------------------------------------------------------- #
#                SCHEMAS DE AVALIAÇÃO E RELACIONADOS A USUÁRIO               #
# -------------------------------------------------------------------------- #


class UserBaseForReview(BaseModel):
    """
    Schema simplificado para exibir informações do autor de uma avaliação.
    Evita expor dados sensíveis do perfil do usuário publicamente.
    """

    id: int
    full_name: str
    model_config = ConfigDict(from_attributes=True)


class ProductReviewBase(BaseModel):
    """Schema base com os campos essenciais de uma avaliação de produto."""

    rating: int = Field(..., gt=0, le=5, description="Nota de 1 a 5 estrelas.")
    comment: Optional[str] = Field(None, max_length=1000)


class ProductReviewCreate(ProductReviewBase):
    """Schema para a criação de uma nova avaliação. Não requer campos adicionais."""

    pass


class ProductReview(ProductReviewBase):
    """Schema de leitura para uma avaliação, incluindo dados do autor."""

    id: int
    author: UserBaseForReview
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                        SCHEMAS DE PRODUTO E CATEGORIA                      #
# -------------------------------------------------------------------------- #


class ProductBase(BaseModel):
    """Schema base com os campos essenciais de um produto."""

    sku: str
    name: str
    image_url: Optional[str] = None
    price: float
    description: Optional[str] = None


class ProductCreate(ProductBase):
    """
    Schema para a criação de um novo produto, incluindo seus dados
    logísticos para cálculo de frete.
    """

    category_id: int
    stock: int = Field(0, ge=0)
    weight_kg: float = Field(..., gt=0, description="Peso do produto em Kg.")
    height_cm: float = Field(..., gt=0, description="Altura do produto em cm.")
    width_cm: float = Field(..., gt=0, description="Largura do produto em cm.")
    length_cm: float = Field(..., gt=0, description="Comprimento do produto em cm.")


class ProductUpdate(BaseModel):
    """
    Schema para a atualização de um produto existente.
    Todos os campos são opcionais para permitir atualizações parciais,
    incluindo os dados de logística.
    """

    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)
    width_cm: Optional[float] = Field(None, gt=0)
    length_cm: Optional[float] = Field(None, gt=0)


class CategoryCreate(BaseModel):
    """Schema para a criação de uma nova categoria."""

    title: str
    description: Optional[str] = None


class CategoryBase(BaseModel):
    """Schema base com os campos essenciais de uma categoria."""

    id: int
    title: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Product(ProductBase):
    """
    Schema de leitura para um produto, incluindo dados de categoria,
    avaliações e informações de logística.
    """

    id: int
    stock: int
    category: CategoryBase
    weight_kg: float
    height_cm: float
    width_cm: float
    length_cm: float
    reviews: List[ProductReview] = []
    model_config = ConfigDict(from_attributes=True)


class Category(CategoryBase):
    """Schema de leitura para uma categoria, incluindo a lista de seus produtos."""

    products: List[Product] = []


Category.model_rebuild()

# -------------------------------------------------------------------------- #
#                         SCHEMAS DE CARRINHO DE COMPRAS                     #
# -------------------------------------------------------------------------- #


class CartItemBase(BaseModel):
    """Schema base para um item de carrinho."""

    quantity: int


class CartItemCreate(BaseModel):
    """Schema para adicionar um item ao carrinho."""

    product_id: int
    quantity: int = Field(1, gt=0)


class CartItemUpdate(BaseModel):
    """
    Schema para atualizar a quantidade de um item no carrinho.
    Permite quantidade >= 0 para tratar a remoção na lógica de negócio.
    """

    quantity: int = Field(ge=0)


class CartItem(CartItemBase):
    """Schema de leitura para um item de carrinho."""

    id: int
    product: Product
    model_config = ConfigDict(from_attributes=True)


class Cart(BaseModel):
    """Schema principal de leitura para o carrinho de um usuário."""

    id: int
    items: List[CartItem] = []
    coupon: Optional[Coupon] = None

    @computed_field
    @property
    def subtotal(self) -> float:
        """Calcula o preço total do carrinho (subtotal) sem descontos."""
        return sum(
            item.product.price * item.quantity for item in self.items if item.product
        )

    @computed_field
    @property
    def discount_amount(self) -> float:
        """Calcula o valor do desconto se um cupom estiver aplicado."""
        if self.coupon:
            return self.subtotal * (self.coupon.discount_percent / 100)
        return 0.0

    @computed_field
    @property
    def final_price(self) -> float:
        """Calcula o preço final do carrinho, aplicando o desconto do cupom."""
        return self.subtotal - self.discount_amount

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                      SCHEMAS DE PEDIDO E ITENS DE PEDIDO                   #
# -------------------------------------------------------------------------- #


class OrderItem(BaseModel):
    """Schema de leitura para um item individual dentro de um pedido."""

    quantity: int
    price_at_purchase: float
    product: Optional[Product]
    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    """Schema base com os campos essenciais de um pedido."""

    id: int
    created_at: datetime
    total_price: float
    status: str
    discount_amount: float
    coupon_code_used: Optional[str] = None
    items: List[OrderItem] = []


class Order(OrderBase):
    """Schema principal de leitura para um pedido de um usuário."""

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                           SCHEMAS DE USUÁRIO E TOKEN                       #
# -------------------------------------------------------------------------- #


class UserBase(BaseModel):
    """Schema base com os dados de perfil de um usuário."""

    email: str
    full_name: str
    cpf: str
    phone: str
    address_street: str
    address_number: str
    address_complement: Optional[str] = None
    address_zip: str
    address_city: str
    address_state: str

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """
        Valida o campo CPF usando a biblioteca `validate_docbr`.
        Retorna o valor original se for válido, ou levanta um `ValueError`.
        """
        cpf_validator = CPF()
        if not cpf_validator.validate(v):
            raise ValueError("CPF fornecido é inválido.")
        return v


class UserCreate(UserBase):
    """Schema para a criação de um usuário, exigindo todos os dados e senha."""

    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """
    Schema para a atualização de dados de perfil de um usuário.

    Todos os campos são opcionais, permitindo que o usuário envie apenas os
    dados que deseja modificar. O e-mail e o CPF não podem ser alterados
    por esta rota para manter a integridade da identificação do usuário.
    """

    full_name: Optional[str] = None
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_zip: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None


class AdminUserUpdate(UserUpdate):
    """
    Schema para a atualização de um usuário por um administrador.

    Herda de `UserUpdate` e adiciona a capacidade de modificar o status de
    `is_active` e `is_superuser`.
    """

    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class User(UserBase):
    """Schema de leitura para um usuário, incluindo ID e status de superuser e ativo."""

    id: int
    is_superuser: bool
    is_active: bool
    orders: List[Order] = []

    model_config = ConfigDict(from_attributes=True)


class AdminOrder(Order):
    """Schema de leitura para um pedido na visão do admin, incluindo o cliente."""

    customer: UserBase


class Token(BaseModel):
    """Schema para o token de acesso JWT."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema para os dados decodificados de dentro de um token JWT."""

    email: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """Schema para a solicitação de recuperação de senha."""

    email: str


class ResetPasswordRequest(BaseModel):
    """Schema para a redefinição de senha com o token."""

    token: str
    new_password: str = Field(..., min_length=6)


class UpdatePasswordRequest(BaseModel):
    """

    Schema para a atualização de senha de um usuário autenticado.

    Exige a senha atual para verificação de segurança, juntamente com
    a nova senha desejada.
    """

    current_password: str
    new_password: str = Field(..., min_length=6)
