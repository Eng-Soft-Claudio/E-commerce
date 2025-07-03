/**
 * @file Página de exibição do histórico de pedidos do usuário.
 * @description Apresenta uma lista de todos os pedidos realizados pelo
 * cliente logado, com detalhes visíveis em um modal.
 */

'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, PackageSearch, Eye, AlertCircle } from 'lucide-react';

import UserAccountLayout from '@/components/user/UserAccountLayout';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface ProductInOrderItem {
  id: number;
  name: string;
}

interface OrderItem {
  quantity: number;
  price_at_purchase: number;
  product: ProductInOrderItem | null;
}

export interface Order {
  id: number;
  created_at: string;
  total_price: number;
  status: string;
  items: OrderItem[];
  discount_amount: number;
  coupon_code_used: string | null;
}

const MeusPedidosPage = () => {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    if (!user) return;
    setPageLoading(true);
    setError(null);

    try {
      const data = await api.getOrders();
      setOrders(data);
    } catch (err) {
      console.error('Erro ao buscar pedidos:', err);
      const message = err instanceof Error ? err.message : 'Falha ao buscar seus pedidos.';
      setError(message);
    } finally {
      setPageLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (!authLoading && user) {
      fetchOrders();
    } else if (!authLoading && !user) {
      router.push('/login?redirect=/meus-pedidos');
    }
  }, [authLoading, user, fetchOrders, router]);

  const renderStatus = (status: string) => {
    const statusConfig: Record<string, { label: string; className: string }> = {
      paid: { label: 'Pago', className: 'bg-green-100 text-green-800 border-green-300' },
      pending_payment: {
        label: 'Pendente',
        className: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      },
      cancelled: { label: 'Cancelado', className: 'bg-red-100 text-red-800 border-red-300' },
      shipped: { label: 'Enviado', className: 'bg-blue-100 text-blue-800 border-blue-300' },
      delivered: {
        label: 'Entregue',
        className: 'bg-purple-100 text-purple-800 border-purple-300',
      },
    };
    const config = statusConfig[status] || {
      label: status,
      className: 'bg-gray-100 text-gray-800',
    };
    return (
      <Badge variant="outline" className={config.className}>
        {config.label}
      </Badge>
    );
  };

  const renderContent = () => {
    if (pageLoading) {
      return (
        <div className="flex items-center justify-center p-10">
          <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
        </div>
      );
    }

    if (error) {
      return (
        <div
          className="p-4 mb-4 text-sm text-red-800 bg-red-100 rounded-lg text-center"
          role="alert"
        >
          <AlertCircle className="mx-auto h-8 w-8 mb-2" />
          <strong>Erro ao carregar pedidos:</strong> {error}
        </div>
      );
    }

    if (orders.length === 0) {
      return (
        <div className="text-center py-10">
          <PackageSearch className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">Nenhum pedido encontrado</h3>
          <p className="mt-1 text-sm text-gray-500">Você ainda não fez nenhuma compra conosco.</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {orders.map((order) => (
          <div key={order.id} className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 p-4 flex justify-between items-center flex-wrap gap-4">
              <div>
                <p className="font-bold text-lg">Pedido #{order.id}</p>
                <p className="text-sm text-gray-500">
                  Realizado em: {new Date(order.created_at).toLocaleDateString('pt-BR')}
                </p>
              </div>
              <div className="text-right">
                {renderStatus(order.status)}
                <p className="font-bold text-xl mt-1 font-mono">
                  R$ {order.total_price.toFixed(2).replace('.', ',')}
                </p>
              </div>
            </div>
            <div className="p-4">
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Eye className="mr-2 h-4 w-4" /> Ver Detalhes
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Detalhes do Pedido #{order.id}</DialogTitle>
                  </DialogHeader>
                  <div className="mt-4">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Produto</TableHead>
                          <TableHead className="text-center">Qtd</TableHead>
                          <TableHead className="text-right">Preço</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {order.items.map((item, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{item.product?.name || '[Produto Removido]'}</TableCell>
                            <TableCell className="text-center">{item.quantity}</TableCell>
                            <TableCell className="text-right font-mono">
                              R$ {item.price_at_purchase.toFixed(2).replace('.', ',')}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    <div className="mt-4 pt-4 border-t text-right space-y-1">
                      {order.coupon_code_used && (
                        <p className="text-sm">
                          Desconto ({order.coupon_code_used}):{' '}
                          <span className="font-mono">
                            - R$ {order.discount_amount.toFixed(2).replace('.', ',')}
                          </span>
                        </p>
                      )}
                      <p className="font-bold text-lg">
                        Total:{' '}
                        <span className="font-mono">
                          R$ {order.total_price.toFixed(2).replace('.', ',')}
                        </span>
                      </p>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <UserAccountLayout>
      <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b pb-4">Meus Pedidos</h2>
      {renderContent()}
    </UserAccountLayout>
  );
};

export default MeusPedidosPage;
