/**
 * @file Página de perfil do usuário.
 * @description Permite que o usuário visualize e atualize suas informações cadastrais, como nome e endereço.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import UserAccountLayout from '@/components/user/UserAccountLayout';
import { UserProfileForm, ProfileFormValues } from '@/components/user/UserProfileForm';

const MinhaContaPage = () => {
  const { user, loading: authLoading, fetchUser } = useAuth();
  const router = useRouter();
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login?redirect=/minha-conta');
    }
  }, [user, authLoading, router]);

  /**
   * Manipula o envio do formulário de atualização de perfil.
   * @param {ProfileFormValues} data
   */
  const handleUpdateProfile = async (data: ProfileFormValues) => {
    setIsUpdating(true);
    setUpdateError(null);
    setUpdateSuccess(null);

    try {
      await api.updateProfile(data);

      await fetchUser();

      setUpdateSuccess('Perfil atualizado com sucesso!');

      setTimeout(() => setUpdateSuccess(null), 3000);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Falha ao atualizar o perfil.';
      console.error('Erro ao atualizar perfil:', err);
      setUpdateError(message);
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
      <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b pb-4">Meu Perfil</h2>

      {/* O formulário agora é renderizado com segurança, pois já validamos que `user` existe */}
      <UserProfileForm user={user} onSubmit={handleUpdateProfile} isLoading={isUpdating} />

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
    </UserAccountLayout>
  );
};

export default MinhaContaPage;
