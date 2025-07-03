/**
 * @file Página para o usuário alterar sua própria senha.
 * @description Fornece um formulário seguro para o usuário autenticado
 * definir uma nova senha, exigindo a senha atual para verificação.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Loader2 } from 'lucide-react';
import { ChangePasswordForm, PasswordFormValues } from '@/components/user/ChangePasswordForm';
import UserAccountLayout from '@/components/user/UserAccountLayout';
import { api } from '@/lib/api';

const ChangePasswordPage = () => {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login?redirect=/minha-conta/alterar-senha');
    }
  }, [user, authLoading, router]);

  /**
   * Lida com o envio do formulário de alteração de senha.
   * @param data Os dados validados do formulário, com a senha atual e a nova.
   */
  const handlePasswordChange = async (data: PasswordFormValues) => {
    setIsUpdating(true);
    setUpdateError(null);
    setUpdateSuccess(null);

    try {
      await api.updatePassword(data);

      setUpdateSuccess(
        'Senha alterada com sucesso! Você será desconectado por segurança em 3 segundos.',
      );

      setTimeout(() => {
        logout();
      }, 3000);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao alterar a senha.';
      setUpdateError(message);
      console.error('Erro ao alterar senha:', err);
    } finally {
      setIsUpdating(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
      </div>
    );
  }

  return (
    <UserAccountLayout>
      <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b pb-4">Alterar Senha</h2>
      <div className="max-w-md">
        <ChangePasswordForm onSubmit={handlePasswordChange} isLoading={isUpdating} />
        {updateError && (
          <p
            className="mt-4 text-sm font-semibold text-center text-red-600 bg-red-100 p-3 rounded-md"
            role="alert"
          >
            {updateError}
          </p>
        )}
        {updateSuccess && (
          <p
            className="mt-4 text-sm font-semibold text-center text-green-600 bg-green-100 p-3 rounded-md"
            role="status"
          >
            {updateSuccess}
          </p>
        )}
      </div>
    </UserAccountLayout>
  );
};

export default ChangePasswordPage;
