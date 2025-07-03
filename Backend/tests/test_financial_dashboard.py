"""
Suíte de Testes para os Relatórios Financeiros do Dashboard.

Testa todos os endpoints sob o prefixo `/admin/dashboard/financial`, garantindo:
1.  Controle de acesso, permitindo apenas superusuários.
2.  Cálculo correto do resumo financeiro (vendas, pedidos, ticket, descontos).
3.  Agregação correta de dados para o gráfico de vendas ao longo do tempo.
4.  Distribuição correta de pedidos por status de pagamento.
5.  Cálculo preciso do desempenho de cupons.
6.  Que os filtros de data funcionem como esperado.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

import pytest
from typing import Dict
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src import models

# -------------------------------------------------------------------------- #
#                                FIXTURES                                    #
# -------------------------------------------------------------------------- #


@pytest.fixture(
    scope="function"
)  # CORREÇÃO: Escopo alterado de "module" para "function"
def setup_orders_for_dashboard(
    client: TestClient,
    superuser_token_headers: Dict,
    db_session: Session,
    test_user: Dict,
):
    """
    Fixture que cria um conjunto rico e variado de dados (categorias,
    produtos, cupons e pedidos) para alimentar os testes do dashboard.
    O escopo é de 'function' para alinhar com as fixtures 'client' e 'db_session'.
    """
    # Criar Categoria e Produtos
    cat_resp = client.post(
        "/categories/", headers=superuser_token_headers, json={"title": "Dash Itens"}
    )
    cat_id = cat_resp.json()["id"]

    product_a_data = {
        "name": "Produto A",
        "sku": "DASH-A",
        "price": 100.0,
        "category_id": cat_id,
        "stock": 100,
        "weight_kg": 1,
        "height_cm": 1,
        "width_cm": 1,
        "length_cm": 1,
    }
    product_b_data = {
        "name": "Produto B",
        "sku": "DASH-B",
        "price": 50.0,
        "category_id": cat_id,
        "stock": 100,
        "weight_kg": 1,
        "height_cm": 1,
        "width_cm": 1,
        "length_cm": 1,
    }

    # CORREÇÃO: Remoção de variáveis não utilizadas
    client.post("/products/", headers=superuser_token_headers, json=product_a_data)
    client.post("/products/", headers=superuser_token_headers, json=product_b_data)

    # Criar Cupons
    client.post(
        "/coupons/",
        headers=superuser_token_headers,
        json={"code": "DASH10", "discount_percent": 10.0},
    )

    # Criar Pedidos em Datas Diferentes e com Status Diferentes
    user_id_for_orders = test_user["id"]
    orders_to_create = [
        # Pedido pago, hoje, com cupom (Total: 90)
        {
            "user_id": user_id_for_orders,
            "status": "paid",
            "created_at": date.today(),
            "total_price": 90.0,
            "coupon_code_used": "DASH10",
            "discount_amount": 10.0,
        },
        # Pedido pago, ontem, sem cupom (Total: 150)
        {
            "user_id": user_id_for_orders,
            "status": "paid",
            "created_at": date.today() - timedelta(days=1),
            "total_price": 150.0,
        },
        # Pedido pendente, hoje (não deve entrar nos cálculos financeiros)
        {
            "user_id": user_id_for_orders,
            "status": "pending_payment",
            "created_at": date.today(),
            "total_price": 50.0,
        },
        # Pedido cancelado, ontem
        {
            "user_id": user_id_for_orders,
            "status": "cancelled",
            "created_at": date.today() - timedelta(days=1),
            "total_price": 100.0,
        },
    ]

    for order_data in orders_to_create:
        db_order = models.Order(**order_data)
        db_session.add(db_order)

    db_session.commit()


# -------------------------------------------------------------------------- #
#                        TESTES DOS ENDPOINTS DO DASHBOARD                   #
# -------------------------------------------------------------------------- #


@pytest.mark.usefixtures("setup_orders_for_dashboard")
class TestFinancialDashboard:
    """Grupo de testes para os relatórios financeiros."""

    def test_get_financial_summary_full_period(
        self, client: TestClient, superuser_token_headers: Dict
    ):
        """Testa o resumo financeiro considerando todos os pedidos pagos."""
        response = client.get(
            "/admin/dashboard/financial/summary", headers=superuser_token_headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total_sales"] == 240.0  # 90 + 150
        assert data["total_orders"] == 2
        assert data["average_ticket"] == 120.0
        assert data["total_discount"] == 10.0

    def test_get_financial_summary_filtered_by_date(
        self, client: TestClient, superuser_token_headers: Dict
    ):
        """Testa o resumo financeiro com filtro de data, pegando apenas o pedido de hoje."""
        today = date.today().isoformat()
        response = client.get(
            f"/admin/dashboard/financial/summary?start_date={today}&end_date={today}",
            headers=superuser_token_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 90.0
        assert data["total_orders"] == 1
        assert data["average_ticket"] == 90.0

    def test_get_sales_over_time_chart(
        self, client: TestClient, superuser_token_headers: Dict
    ):
        """Testa a geração de dados para o gráfico de vendas."""
        response = client.get(
            "/admin/dashboard/financial/sales-over-time",
            headers=superuser_token_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()

        # O número exato de dias depende de quando os testes são rodados
        assert len(data) >= 1

        yesterday_str = str(date.today() - timedelta(days=1))
        today_str = str(date.today())

        yesterday_data = next(
            (item for item in data if item["date"] == yesterday_str), None
        )
        today_data = next((item for item in data if item["date"] == today_str), None)

        if yesterday_data:
            assert yesterday_data["total_sales"] == 150.0
        if today_data:
            assert today_data["total_sales"] == 90.0

    def test_get_payment_status_distribution(
        self, client: TestClient, superuser_token_headers: Dict
    ):
        """Testa a distribuição de pedidos por status."""
        response = client.get(
            "/admin/dashboard/financial/payment-status", headers=superuser_token_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["paid"] == 2
        assert data["pending_payment"] == 1
        assert data["cancelled"] == 1
        assert data["shipped"] == 0
        assert data["delivered"] == 0

    def test_get_coupon_performance(
        self, client: TestClient, superuser_token_headers: Dict
    ):
        """Testa o relatório de desempenho dos cupons."""
        response = client.get(
            "/admin/dashboard/financial/coupon-performance",
            headers=superuser_token_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["code"] == "DASH10"
        assert data[0]["times_used"] == 1
        assert data[0]["total_discount"] == 10.0

    def test_dashboard_access_by_common_user_is_forbidden(
        self, client: TestClient, user_token_headers: Dict
    ):
        """Garante que um usuário comum não pode acessar os endpoints do dashboard."""
        response = client.get(
            "/admin/dashboard/financial/summary", headers=user_token_headers
        )
        assert response.status_code == 403
