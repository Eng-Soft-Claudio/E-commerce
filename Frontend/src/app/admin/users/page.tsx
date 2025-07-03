/**
 * @file Página administrativa para gerenciamento de clientes.
 * @description Permite que superusuários visualizem, ativem/desativem e deletem contas de clientes.
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
import { Loader2, Users, Trash2, CheckCircle, Ban, AlertCircle } from 'lucide-react';

import AdminLayout from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ClientUser {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  orders: { id: number }[];
}

/**
 * Componente principal da página de gerenciamento de clientes.
 */
const AdminUsersPage = () => {
  const [users, setUsers] = useState<ClientUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = Cookies.get('access_token');
      if (!token) throw new Error('Token de autenticação não encontrado.');

      const response = await fetch(`${API_URL}/admin/users/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error(`Falha ao buscar usuários: ${response.statusText}`);
      }
      const data: ClientUser[] = await response.json();
      setUsers(data);
    } catch (err) {
      console.error('Erro ao buscar usuários:', err);
      const message = err instanceof Error ? err.message : 'Ocorreu um erro desconhecido.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleToggleActive = async (user: ClientUser) => {
    const token = Cookies.get('access_token');
    const newStatus = !user.is_active;

    try {
      const response = await fetch(`${API_URL}/admin/users/${user.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ is_active: newStatus }),
      });

      if (!response.ok) {
        throw new Error('Falha ao atualizar o status do usuário.');
      }

      setUsers((currentUsers) =>
        currentUsers.map((u) => (u.id === user.id ? { ...u, is_active: newStatus } : u)),
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Um erro inesperado ocorreu.';
      alert(`Erro ao alterar o status do usuário: ${message}`);
      console.error(error);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (
      !window.confirm(
        `Tem certeza que deseja DELETAR PERMANENTEMENTE o usuário com ID ${userId}? Esta ação não pode ser desfeita.`,
      )
    )
      return;

    const token = Cookies.get('access_token');
    try {
      const response = await fetch(`${API_URL}/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Falha ao deletar usuário.');
      }

      if (data.message) alert(data.message);

      await fetchUsers();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Um erro inesperado ocorreu.';
      alert(`Erro: ${message}`);
      console.error(error);
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="text-center p-10">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-gray-500" />
        </div>
      );
    }
    if (error) {
      return (
        <div className="text-center py-10 text-red-600" role="alert">
          <AlertCircle className="mx-auto h-10 w-10" />
          <p className="mt-4">
            <strong>Erro ao carregar clientes:</strong> {error}
          </p>
        </div>
      );
    }
    if (users.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <Users className="h-12 w-12 text-gray-400 mb-3" />
          <h2 className="text-xl font-semibold">Nenhum cliente encontrado</h2>
        </div>
      );
    }
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Nome Completo</TableHead>
            <TableHead>Email</TableHead>
            <TableHead className="text-center">Pedidos</TableHead>
            <TableHead className="text-center">Status</TableHead>
            <TableHead className="text-center">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {users.map((user) => (
            <TableRow
              key={user.id}
              className={!user.is_active ? 'bg-red-50 hover:bg-red-100/50' : ''}
            >
              <TableCell className="font-medium">{user.id}</TableCell>
              <TableCell>{user.full_name}</TableCell>
              <TableCell>{user.email}</TableCell>
              <TableCell className="text-center">{user.orders?.length || 0}</TableCell>
              <TableCell className="text-center">
                <div className="flex items-center justify-center space-x-2">
                  <Switch
                    checked={user.is_active}
                    onCheckedChange={() => handleToggleActive(user)}
                    aria-label={`Ativar ou desativar usuário ${user.full_name}`}
                  />
                  <Badge variant={user.is_active ? 'secondary' : 'destructive'}>
                    {user.is_active ? (
                      <>
                        <CheckCircle className="h-3 w-3 mr-1" /> Ativo
                      </>
                    ) : (
                      <>
                        <Ban className="h-3 w-3 mr-1" /> Inativo
                      </>
                    )}
                  </Badge>
                </div>
              </TableCell>
              <TableCell className="text-center space-x-2">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDeleteUser(user.id)}
                  aria-label={`Deletar usuário ${user.full_name}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
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
        <h1 className="text-2xl font-bold text-gray-800">Gerenciar Clientes</h1>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md overflow-x-auto">{renderContent()}</div>
    </AdminLayout>
  );
};

export default AdminUsersPage;
