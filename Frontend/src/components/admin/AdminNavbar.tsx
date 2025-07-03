/**
 * @file Componente Navbar para o Painel de Administração.
 * @description Renderiza a barra de navegação superior do layout administrativo,
 * exibindo a mensagem de boas-vindas ao usuário e o botão de logout.
 */

'use client';

import React from 'react';
import { LogOut } from 'lucide-react';

import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';

/**
 * Componente de cliente que busca o usuário do AuthContext para renderizar
 * a barra de navegação superior do administrador.
 */
const AdminNavbar = () => {
  const { user, logout } = useAuth();

  if (!user) {
    return (
      <header className="bg-white shadow-md p-4 flex justify-end items-center h-[68px]">
        <div className="animate-pulse flex items-center gap-4">
          <div className="h-4 bg-gray-200 rounded-md w-48"></div>
          <div className="h-8 bg-gray-200 rounded-md w-20"></div>
        </div>
      </header>
    );
  }

  return (
    <header className="bg-white shadow-md p-4 flex justify-between items-center">
      <div></div>

      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-700 hidden sm:inline">Bem-vindo, {user.full_name}</span>
        <Button variant="outline" size="sm" onClick={logout}>
          <LogOut className="mr-2 h-4 w-4" />
          Sair
        </Button>
      </div>
    </header>
  );
};

export default AdminNavbar;
