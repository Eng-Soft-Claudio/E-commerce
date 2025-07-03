/**
 * @file Página administrativa para gerenciamento de pedidos.
 * @description Permite que superusuários visualizem todos os pedidos, vejam seus detalhes e alterem seus status.
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Cookies from 'js-cookie';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Loader2, PackageSearch, Eye, AlertCircle } from 'lucide-react';

import AdminLayout from '@/components/admin/AdminLayout';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ProductInOrderItem {
  id: number;
  name: string;
}

interface OrderItem {
  quantity: number;
  price_at_purchase: number;
  product: ProductInOrderItem | null;
}

interface UserInOrder {
  id: number;
  email: string;
  full_name: string;
}

interface AdminOrder {
  id: number;
  created_at: string;
  total_price: number;
  discount_amount: number;
  coupon_code_used: string | null;
  status: string;
  customer: UserInOrder;
  items: OrderItem[];
}

const AdminOrdersPage = () => {
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<AdminOrder | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = Cookies.get('access_token');
      if (!token) throw new Error('Token de autenticação não encontrado.');

      const response = await fetch(`${API_URL}/orders/admin/all`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `Erro HTTP ${response.status}`);
      }

      const data: AdminOrder[] = await response.json();
      setOrders(data);
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Falha ao carregar os pedidos.';
      console.error('Erro ao buscar pedidos:', e);
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleStatusChange = async (orderId: number, newStatus: string) => {
    if (!window.confirm(`Tem certeza que deseja alterar o status para "${newStatus}"?`)) return;

    setIsUpdating(true);
    const token = Cookies.get('access_token');
    try {
      const response = await fetch(`${API_URL}/orders/${orderId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!response.ok) throw new Error('Falha ao atualizar o status.');

      const updatedOrder = await response.json();
      setOrders((currentOrders) =>
        currentOrders.map((o) => (o.id === orderId ? { ...o, status: updatedOrder.status } : o)),
      );
      setSelectedOrder((currentOrder) =>
        currentOrder ? { ...currentOrder, status: updatedOrder.status } : null,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro inesperado.';
      alert(`Erro ao atualizar o status: ${message}`);
      console.error(error);
    } finally {
      setIsUpdating(false);
    }
  };

  const renderStatus = (status: string) => {
    const statusConfig: Record<string, { label: string; className: string }> = {
      paid: { label: 'Pago', className: 'bg-green-600 hover:bg-green-700 text-white' },
      pending_payment: { label: 'Pendente', className: 'bg-yellow-600 text-white' },
      cancelled: { label: 'Cancelado', className: '' },
      shipped: { label: 'Enviado', className: 'bg-blue-600 hover:bg-blue-700 text-white' },
      delivered: { label: 'Entregue', className: 'bg-purple-600 hover:bg-purple-700 text-white' },
    };
    const config = statusConfig[status];
    if (!config) return <Badge variant="outline">{status}</Badge>;

    return (
      <Badge
        variant={status === 'cancelled' ? 'destructive' : 'secondary'}
        className={config.className}
      >
        {config.label}
      </Badge>
    );
  };

  const renderMainContent = () => {
    if (loading)
      return (
        <div className="flex justify-center py-10">
          <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
        </div>
      );
    if (error)
      return (
        <div className="text-center py-10 text-red-600" role="alert">
          <AlertCircle className="mx-auto h-8 w-8 mb-2" />
          <p>
            <strong>Erro ao carregar pedidos:</strong> {error}
          </p>
        </div>
      );
    if (orders.length === 0)
      return (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <PackageSearch className="h-12 w-12 text-gray-400 mb-3" />
          <h2 className="text-xl font-semibold">Nenhum pedido encontrado</h2>
          <p className="text-gray-500 mt-1">Ainda não há pedidos registrados no sistema.</p>
        </div>
      );
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[10%]">Pedido ID</TableHead>
            <TableHead className="w-[30%]">Cliente</TableHead>
            <TableHead className="w-[20%]">Data</TableHead>
            <TableHead className="w-[15%] text-center">Status</TableHead>
            <TableHead className="w-[15%] text-right">Valor Total</TableHead>
            <TableHead className="w-[10%] text-center">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.map((order) => (
            <TableRow key={order.id}>
              <TableCell className="font-medium">#{order.id}</TableCell>
              <TableCell>{order.customer.full_name}</TableCell>
              <TableCell>{new Date(order.created_at).toLocaleDateString('pt-BR')}</TableCell>
              <TableCell className="text-center">{renderStatus(order.status)}</TableCell>
              <TableCell className="text-right font-mono">
                R$ {order.total_price.toFixed(2).replace('.', ',')}
              </TableCell>
              <TableCell className="text-center">
                <DialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedOrder(order)}
                    aria-label={`Ver detalhes do pedido ${order.id}`}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </DialogTrigger>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  };

  return (
    <AdminLayout>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-800">Gerenciar Pedidos</h1>
      </div>

      <Dialog onOpenChange={(isOpen) => !isOpen && setSelectedOrder(null)}>
        <div className="bg-white p-6 rounded-lg shadow-md overflow-x-auto">
          {renderMainContent()}
        </div>

        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Detalhes do Pedido #{selectedOrder?.id}</DialogTitle>
          </DialogHeader>
          {selectedOrder && (
            <div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 mb-6 text-sm">
                <div>
                  <strong>Cliente:</strong> {selectedOrder.customer.full_name}
                </div>
                <div>
                  <strong>Email:</strong> {selectedOrder.customer.email}
                </div>
                <div>
                  <strong>Data:</strong>{' '}
                  {new Date(selectedOrder.created_at).toLocaleString('pt-BR')}
                </div>
                <div className="flex items-center gap-2">
                  <strong>Status Atual:</strong> {renderStatus(selectedOrder.status)}
                </div>
                <div>
                  <strong>Cupom Usado:</strong> {selectedOrder.coupon_code_used || 'Nenhum'}
                </div>
                <div>
                  <strong>Desconto:</strong>{' '}
                  <span className="font-mono">
                    R$ {selectedOrder.discount_amount.toFixed(2).replace('.', ',')}
                  </span>
                </div>
                <div className="col-span-2 pt-2 border-t mt-2">
                  <strong className="text-base">
                    Valor Total:{' '}
                    <span className="font-mono">
                      R$ {selectedOrder.total_price.toFixed(2).replace('.', ',')}
                    </span>
                  </strong>
                </div>
              </div>

              <h3 className="font-bold mb-2">Itens do Pedido:</h3>
              <div className="border rounded-md">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Produto</TableHead>
                      <TableHead className="text-center">Qtd.</TableHead>
                      <TableHead className="text-right">Preço Unitário</TableHead>
                      <TableHead className="text-right">Subtotal</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedOrder.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          {item.product?.name || (
                            <span className="text-red-500 italic">[Produto Removido]</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center">{item.quantity}</TableCell>
                        <TableCell className="text-right font-mono">
                          R$ {item.price_at_purchase.toFixed(2).replace('.', ',')}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          R$ {(item.price_at_purchase * item.quantity).toFixed(2).replace('.', ',')}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="mt-6">
                <h3 className="font-bold mb-2">Alterar Status:</h3>
                <div className="flex flex-wrap gap-2">
                  {['pending_payment', 'paid', 'shipped', 'delivered', 'cancelled'].map(
                    (status) => {
                      const config = { label: status, ...renderStatus(status).props };
                      return (
                        <Button
                          key={status}
                          size="sm"
                          variant={config.variant || 'secondary'}
                          className={config.className}
                          onClick={() => handleStatusChange(selectedOrder!.id, status)}
                          disabled={isUpdating || selectedOrder.status === status}
                        >
                          Marcar como {config.label.toLowerCase()}
                        </Button>
                      );
                    },
                  )}
                </div>
                {isUpdating && <Loader2 className="mt-2 h-4 w-4 animate-spin" />}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </AdminLayout>
  );
};

export default AdminOrdersPage;
