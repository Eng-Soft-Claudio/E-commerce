/**
 * @file Componente de Menu de Navegação para Dispositivos Móveis.
 * @description Renderiza um painel lateral (off-canvas) com links de navegação
 * e ações, gerenciado por um estado de visibilidade controlado pelo componente pai.
 */

'use client';

import React, { ReactNode } from 'react';
import Link from 'next/link';
import { X, User, LogOut } from 'lucide-react';

import { useAuth } from '@/context/AuthContext';
import { cn } from '@/lib/utils';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  children?: ReactNode;
}

const MobileMenu = ({ isOpen, onClose, children }: MobileMenuProps) => {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    onClose();
  };

  return (
    <div
      className={cn(
        'fixed inset-0 z-40 lg:hidden transition-opacity duration-300',
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none',
      )}
      role="dialog"
      aria-modal="true"
      aria-labelledby="mobile-menu-title"
    >
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden="true" />
      <div
        className={cn(
          'relative w-4/5 max-w-sm bg-white h-full shadow-xl transform transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 flex flex-col h-full">
          <div className="flex justify-between items-center mb-6 flex-shrink-0">
            <h2 id="mobile-menu-title" className="text-xl font-bold text-gray-900">
              Menu
            </h2>
            <button
              onClick={onClose}
              className="p-1 text-gray-500 hover:text-red-500"
              aria-label="Fechar menu"
            >
              <X size={24} />
            </button>
          </div>
          {children}
          <nav className="space-y-6 overflow-y-auto mt-4 flex-grow">
            {user ? (
              <div>
                <h3 className="font-bold text-lg mb-2 border-b pb-2">MINHA CONTA</h3>
                <ul>
                  <li>
                    <Link
                      onClick={onClose}
                      href="/minha-conta"
                      className="flex items-center gap-3 text-gray-700 hover:text-black block py-3"
                    >
                      <User size={18} /> Meu Perfil
                    </Link>
                  </li>
                  <li>
                    <Link
                      onClick={onClose}
                      href="/meus-pedidos"
                      className="flex items-center gap-3 text-gray-700 hover:text-black block py-3"
                    >
                      Meus Pedidos
                    </Link>
                  </li>
                  <li>
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-3 text-red-600 hover:text-red-800 w-full text-left py-3"
                    >
                      <LogOut size={18} /> Sair
                    </button>
                  </li>
                </ul>
              </div>
            ) : (
              <div>
                <h3 className="font-bold text-lg mb-2 border-b pb-2">ACESSO</h3>
                <Link
                  onClick={onClose}
                  href="/login"
                  className="flex items-center gap-3 text-gray-700 hover:text-black block py-3"
                >
                  <User size={18} /> Entrar ou Cadastrar
                </Link>
              </div>
            )}
            <div>
              <h3 className="font-bold text-lg mb-2 border-b pb-2">LOJA</h3>
              <ul>
                <li>
                  <Link
                    onClick={onClose}
                    href="/"
                    className="text-gray-700 hover:text-black block py-3"
                  >
                    Página Inicial
                  </Link>
                </li>
                <li>
                  <Link
                    onClick={onClose}
                    href="#"
                    className="text-gray-700 hover:text-black block py-3"
                  >
                    Todas as Categorias
                  </Link>
                </li>
              </ul>
            </div>
          </nav>
        </div>
      </div>
    </div>
  );
};

export default MobileMenu;
