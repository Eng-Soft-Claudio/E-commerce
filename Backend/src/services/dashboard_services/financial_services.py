"""
Módulo de Serviço para Relatórios Financeiros do Dashboard.

Este módulo contém as funções que realizam as consultas complexas ao banco de
dados para extrair e processar dados financeiros. A lógica de negócio para
cálculo de vendas, desempenho de cupons e ticket médio reside aqui, mantendo
os roteadores limpos e focados apenas na exposição dos dados.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from datetime import datetime, timedelta, date  # noqa: F401
from typing import Dict, Any, List

from sqlalchemy import func, case  # noqa: F401
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text

from ... import models

# -------------------------------------------------------------------------- #
#                             DEFINIÇÕES DE PERÍODOS                         #
# -------------------------------------------------------------------------- #

PERIODS: Dict[str, date] = {
    "daily": date.today(),
    "weekly": date.today() - timedelta(days=date.today().weekday()),
    "monthly": date.today().replace(day=1),
}

# -------------------------------------------------------------------------- #
#                       FUNÇÕES DE LÓGICA DE RELATÓRIOS                      #
# -------------------------------------------------------------------------- #


def get_financial_summary(
    db: Session, start_date: date | None, end_date: date | None
) -> Dict[str, Any]:
    """
    Calcula e retorna um resumo financeiro com base em um período.

    Args:
        db (Session): A sessão do banco de dados.
        start_date (date | None): A data de início do filtro.
        end_date (date | None): A data de término do filtro.

    Returns:
        Dict[str, Any]: Um dicionário contendo o total de vendas,
                        total de pedidos, ticket médio e desconto total.
    """
    query = db.query(
        func.sum(models.Order.total_price),
        func.count(models.Order.id),
        func.sum(models.Order.discount_amount),
    ).filter(models.Order.status == "paid")

    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    if end_date:
        query = query.filter(models.Order.created_at < (end_date + timedelta(days=1)))

    total_sales, total_orders, total_discount = query.one()

    total_sales = total_sales or 0
    total_orders = total_orders or 0
    total_discount = total_discount or 0
    average_ticket = (total_sales / total_orders) if total_orders > 0 else 0

    return {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "average_ticket": average_ticket,
        "total_discount": total_discount,
    }


def get_sales_over_time_chart(
    db: Session, period_key: str = "monthly"
) -> List[Dict[str, Any]]:
    """
    Prepara os dados para um gráfico de vendas ao longo do tempo.

    Agrupa as vendas por dia para um determinado período (diário, semanal
    ou mensal) para fácil visualização em um gráfico de linhas.

    Args:
        db (Session): A sessão do banco de dados.
        period_key (str): A chave do período ('daily', 'weekly', 'monthly').

    Returns:
        List[Dict[str, Any]]: Uma lista de dicionários, cada um com 'date' e
                              'total_sales' para aquele dia.
    """
    start_date = PERIODS.get(period_key, PERIODS["monthly"])

    sales_data = (
        db.query(
            func.date(models.Order.created_at).label("sale_date"),
            func.sum(models.Order.total_price).label("daily_sales"),
        )
        .filter(models.Order.status == "paid")
        .filter(models.Order.created_at >= start_date)
        .group_by("sale_date")
        .order_by("sale_date")
        .all()
    )

    return [
        {"date": str(row.sale_date), "total_sales": row.daily_sales or 0}
        for row in sales_data
    ]


def get_payment_status_distribution(db: Session) -> Dict[str, int]:
    """
    Retorna a contagem de pedidos para cada status de pagamento.

    Args:
        db (Session): A sessão do banco de dados.

    Returns:
        Dict[str, int]: Um dicionário mapeando cada status de pagamento para
                        a sua contagem de pedidos.
    """
    status_query_result = (
        db.query(models.Order.status, func.count(models.Order.id))
        .group_by(models.Order.status)
        .all()
    )

    all_statuses = ["pending_payment", "paid", "shipped", "delivered", "cancelled"]
    result = {status: 0 for status in all_statuses}
    result.update({status: count for status, count in status_query_result})

    return result


def get_coupon_performance(db: Session) -> List[Dict[str, Any]]:
    """
    Retorna estatísticas de uso para cada cupom.

    Calcula a quantidade de vezes que um cupom foi usado e o total de
    desconto que ele gerou.

    Args:
        db (Session): A sessão do banco de dados.

    Returns:
        List[Dict[str, Any]]: Uma lista dos cupons, com seu código,
                              número de usos e desconto total.
    """
    coupon_data = (
        db.query(
            models.Order.coupon_code_used,
            func.count(models.Order.id).label("times_used"),
            func.sum(models.Order.discount_amount).label("total_discount"),
        )
        .filter(models.Order.coupon_code_used.isnot(None))
        .group_by(models.Order.coupon_code_used)
        .order_by(text("times_used DESC"))
        .all()
    )

    return [
        {
            "code": row.coupon_code_used,
            "times_used": row.times_used,
            "total_discount": row.total_discount,
        }
        for row in coupon_data
    ]
