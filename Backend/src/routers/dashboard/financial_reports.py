"""
Módulo de Roteamento para Relatórios Financeiros do Dashboard.

Expõe endpoints protegidos para que administradores possam consumir dados
e métricas financeiras agregadas da loja, como resumos de vendas, gráficos
e desempenho de cupons.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import Dict, Any, List, Optional  # noqa: F401
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ... import auth, schemas
from ...database import get_db
from ...services.dashboard_services import financial_services

# -------------------------------------------------------------------------- #
#                             DEFINIÇÕES DE SCHEMA                           #
# -------------------------------------------------------------------------- #

# Estes poderiam estar em um arquivo de schemas específico para o dashboard,
# mas para simplicidade inicial, vamos mantê-los aqui.

class FinancialSummaryResponse(schemas.BaseModel):
    """Schema para a resposta do resumo financeiro."""
    total_sales: float
    total_orders: int
    average_ticket: float
    total_discount: float

class SalesOverTimePoint(schemas.BaseModel):
    """Schema para um único ponto de dados no gráfico de vendas."""
    date: str
    total_sales: float

class CouponPerformanceResponse(schemas.BaseModel):
    """Schema para a resposta do desempenho de um único cupom."""
    code: str
    times_used: int
    total_discount: float


# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/admin/dashboard/financial",
    tags=["Admin Dashboard: Financial Reports"],
    dependencies=[Depends(auth.get_current_superuser)],
)

# -------------------------------------------------------------------------- #
#                             ENDPOINTS DE RELATÓRIOS                        #
# -------------------------------------------------------------------------- #


@router.get(
    "/summary",
    response_model=FinancialSummaryResponse,
    summary="Obtém um resumo financeiro geral",
)
def get_financial_summary_endpoint(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Retorna um resumo das principais métricas financeiras (vendas totais,
    número de pedidos, ticket médio e descontos) para um intervalo de
    datas opcional. Se nenhuma data for fornecida, considera todos os dados.
    """
    summary = financial_services.get_financial_summary(
        db, start_date=start_date, end_date=end_date
    )
    return summary


@router.get(
    "/sales-over-time",
    response_model=List[SalesOverTimePoint],
    summary="Obtém dados para o gráfico de vendas ao longo do tempo",
)
def get_sales_chart_endpoint(
    period: str = Query(
        "monthly", enum=["daily", "weekly", "monthly"], description="Período do gráfico"
    ),
    db: Session = Depends(get_db),
):
    """
    Fornece os dados agregados por dia para construir um gráfico de
    evolução das vendas.
    """
    chart_data = financial_services.get_sales_over_time_chart(db, period_key=period)
    return chart_data


@router.get(
    "/payment-status",
    response_model=Dict[str, int],
    summary="Obtém a distribuição de pedidos por status de pagamento",
)
def get_payment_status_endpoint(db: Session = Depends(get_db)):
    """
    Retorna um dicionário com a contagem de pedidos para cada status
    de pagamento possível (pago, pendente, cancelado, etc.), ideal
    para um gráfico de pizza.
    """
    distribution = financial_services.get_payment_status_distribution(db)
    return distribution


@router.get(
    "/coupon-performance",
    response_model=List[CouponPerformanceResponse],
    summary="Lista o desempenho dos cupons de desconto utilizados",
)
def get_coupon_performance_endpoint(db: Session = Depends(get_db)):
    """
    Retorna uma lista de todos os cupons que já foram utilizados em pedidos,
    quantificando quantas vezes cada um foi usado e o montante total de
    desconto que cada um gerou.
    """
    performance_data = financial_services.get_coupon_performance(db)
    return performance_data