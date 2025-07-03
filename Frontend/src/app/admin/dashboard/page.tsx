/**
 * @file Página de Dashboard Financeiro para Administradores.
 * @description Apresenta um resumo de métricas financeiras chave e visualizações
 * de dados como vendas ao longo do tempo e distribuição de status de pedidos.
 */

'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import Cookies from 'js-cookie';
import { CreditCard, ShoppingBag, Users, Percent, Loader2, AlertCircle } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import AdminLayout from '@/components/admin/AdminLayout';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FinancialSummary {
  total_sales: number;
  total_orders: number;
  average_ticket: number;
  total_discount: number;
}
interface SalesOverTimePoint {
  date: string;
  total_sales: number;
}
interface PaymentStatusDist {
  [key: string]: number;
}

const formatCurrency = (value: number) => `R$ ${value.toFixed(2).replace('.', ',')}`;
const formatChartDate = (tick: string) =>
  new Date(tick + 'T00:00:00').toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
  });

/**
 * Componente principal da página de Dashboard Financeiro.
 */
const DashboardPage = () => {
  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [salesChartData, setSalesChartData] = useState<SalesOverTimePoint[]>([]);
  const [statusDistribution, setStatusDistribution] = useState<PaymentStatusDist>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const token = Cookies.get('access_token');
    if (!token) {
      setError('Token de autenticação não encontrado. Faça o login novamente.');
      setLoading(false);
      return;
    }
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const endpoints = [
        `${API_URL}/admin/dashboard/financial/summary`,
        `${API_URL}/admin/dashboard/financial/sales-over-time?period=monthly`,
        `${API_URL}/admin/dashboard/financial/payment-status`,
      ];

      const responses = await Promise.all(endpoints.map((url) => fetch(url, { headers })));

      for (const res of responses) {
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || `Falha na requisição para ${res.url}`);
        }
      }

      const [summaryData, salesChartData, statusData] = await Promise.all(
        responses.map((res) => res.json()),
      );

      setSummary(summaryData);
      setSalesChartData(salesChartData);
      setStatusDistribution(statusData);
    } catch (err) {
      console.error('Erro ao carregar dados do dashboard:', err);
      const message =
        err instanceof Error ? err.message : 'Erro inesperado ao carregar o dashboard.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllDashboardData();
  }, [fetchAllDashboardData]);

  const paymentStatusChartData = useMemo(() => {
    const statusLabels: Record<string, string> = {
      pending_payment: 'Pendente',
      paid: 'Pago',
      shipped: 'Enviado',
      delivered: 'Entregue',
      cancelled: 'Cancelado',
    };
    return Object.entries(statusDistribution)
      .map(([status, count]) => ({
        name: statusLabels[status] || status,
        value: count,
      }))
      .filter((item) => item.value > 0);
  }, [statusDistribution]);

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-10 w-10 animate-spin text-gray-500" />
          <p className="ml-4 text-lg text-gray-600">Carregando dados do dashboard...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div
          className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center"
          role="alert"
        >
          <AlertCircle className="h-6 w-6 mr-3" />
          <div>
            <p className="font-bold">Não foi possível carregar o dashboard.</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      );
    }

    if (summary) {
      return (
        <>
          {/* PAINEL DE MÉTRICAS PRINCIPAIS */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              icon={CreditCard}
              title="Vendas Totais (pagas)"
              value={formatCurrency(summary.total_sales)}
              color="green"
            />
            <StatCard
              icon={ShoppingBag}
              title="Total de Pedidos (pagos)"
              value={summary.total_orders}
              color="blue"
            />
            <StatCard
              icon={Users}
              title="Ticket Médio"
              value={formatCurrency(summary.average_ticket)}
              color="purple"
            />
            <StatCard
              icon={Percent}
              title="Total de Descontos"
              value={formatCurrency(summary.total_discount)}
              color="yellow"
            />
          </div>

          {/* GRÁFICOS */}
          <div className="mt-8 grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Vendas no Mês</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={salesChartData}
                  margin={{ top: 5, right: 20, left: -10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={formatChartDate} />
                  <YAxis />
                  <Tooltip formatter={(value: number) => [formatCurrency(value), 'Vendas']} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="total_sales"
                    name="Vendas"
                    stroke="#16a34a"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-800 mb-4">
                Distribuição de Status de Pedidos
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={paymentStatusChartData}
                  layout="vertical"
                  margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={80} />
                  <Tooltip
                    cursor={{ fill: '#f3f4f6' }}
                    formatter={(value: number) => [value, 'Pedidos']}
                  />
                  <Bar dataKey="value" name="Total de Pedidos" fill="#3b82f6" barSize={30} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      );
    }
    return <p className="mt-4 text-gray-600">Nenhum dado financeiro disponível para exibição.</p>;
  };

  return (
    <AdminLayout>
      <h1 className="text-3xl font-bold text-gray-800 mb-8">Dashboard Financeiro</h1>
      {renderContent()}
    </AdminLayout>
  );
};

interface StatCardProps {
  icon: React.ElementType;
  title: string;
  value: string | number;
  color: 'green' | 'blue' | 'purple' | 'yellow';
}

const StatCard = ({ icon: Icon, title, value, color }: StatCardProps) => {
  const colorClasses = {
    green: 'bg-green-100 text-green-600',
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    yellow: 'bg-yellow-100 text-yellow-600',
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md flex items-center space-x-4">
      <div className={`p-3 rounded-full ${colorClasses[color]}`}>
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <h3 className="text-gray-500 text-sm">{title}</h3>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
};

export default DashboardPage;
