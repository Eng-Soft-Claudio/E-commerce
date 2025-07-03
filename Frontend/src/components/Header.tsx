/**
 * @file Componente Header principal da aplicação.
 * @description Inclui o logo, a barra de busca, navegação do usuário e o gatilho para o menu móvel.
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Menu, ShoppingCart, User as UserIcon, LogOut, Search } from 'lucide-react';

import MobileMenu from './MobileMenu';
import { useAuth } from '@/context/AuthContext';
import { Input } from '@/components/ui/input';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { user, logout, cart } = useAuth();
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
      if (isMenuOpen) {
        setIsMenuOpen(false);
      }
    }
  };

  const cartValue = user && !user.is_superuser && cart ? cart.final_price : 0;

  return (
    <>
      <header className="bg-white text-black shadow-md sticky top-0 z-30">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-20 gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsMenuOpen(true)}
                className="lg:hidden"
                aria-label="Abrir menu"
              >
                <Menu className="h-6 w-6" />
              </button>
              <div className="text-xl md:text-3xl font-bold">
                <Link href="/" className="hover:text-gray-400">
                  E-Commerce
                </Link>
              </div>
            </div>

            <div className="hidden lg:flex flex-grow max-w-lg">
              <form onSubmit={handleSearchSubmit} className="w-full relative">
                <Input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="O que você está procurando?"
                  className="w-full bg-gray-100 border-gray-300 rounded-lg py-2 pl-10 pr-4 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
                />
                <button
                  type="submit"
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                  aria-label="Buscar"
                >
                  <Search className="h-5 w-5" />
                </button>
              </form>
            </div>

            <div className="flex items-center space-x-4 shrink-0">
              {user ? (
                <>
                  <Link
                    href={user.is_superuser ? '/admin/dashboard' : '/minha-conta'}
                    className="hidden md:flex items-center space-x-2 hover:text-red-500"
                  >
                    <UserIcon className="h-5 w-5" />
                    <span className="hidden lg:inline">Olá, {user.full_name.split(' ')[0]}</span>
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="hidden md:flex items-center space-x-2 hover:text-red-500"
                    aria-label="Sair"
                  >
                    <LogOut className="h-5 w-5" />
                  </button>
                </>
              ) : (
                <Link href="/login" className="flex items-center space-x-2 hover:text-red-500">
                  <UserIcon className="h-5 w-5" />
                  <span className="hidden md:inline">Entrar</span>
                </Link>
              )}

              <div className="h-6 w-px bg-gray-300"></div>

              <Link href="/cart" className="flex items-center space-x-2 hover:text-red-500">
                <ShoppingCart className="h-5 w-5" />
                <span className="font-mono">{`R$${cartValue.toFixed(2).replace('.', ',')}`}</span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <MobileMenu isOpen={isMenuOpen} onClose={() => setIsMenuOpen(false)}>
        <div className="px-6 py-4 border-t border-gray-200">
          <form onSubmit={handleSearchSubmit} className="w-full relative">
            <Input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar produtos..."
              className="w-full bg-gray-100 border-gray-300 rounded-lg py-2 pl-10 pr-4"
            />
            <button
              type="submit"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              aria-label="Buscar"
            >
              <Search className="h-5 w-5" />
            </button>
          </form>
        </div>
      </MobileMenu>
    </>
  );
};

export default Header;
