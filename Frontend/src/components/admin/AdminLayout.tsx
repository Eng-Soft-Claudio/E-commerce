/**
 * @file Layout principal para as páginas da área administrativa.
 * @description Provê a estrutura com menu lateral fixo e o contêiner de
 * conteúdo para todas as páginas do painel de administração.
 */

'use client';

import React, { ReactNode, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { LayoutDashboard, Box, ShoppingBag, Users, FolderKanban, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import AdminNavbar from './AdminNavbar';

interface NavItemProps {
  href: string;
  icon: React.ElementType;
  children: ReactNode;
}

/**
 * Subcomponente para renderizar um item do menu de navegação lateral.
 * Inclui lógica para destacar o link ativo.
 */
const AdminNavItem = ({ href, icon: Icon, children }: NavItemProps) => {
  const pathname = usePathname();
  const isActive = pathname.startsWith(href);

  return (
    <Link
      href={href}
      className={cn(
        'flex items-center px-4 py-2.5 rounded-lg transition-colors',
        isActive ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700/50 hover:text-white',
      )}
    >
      <Icon className="mr-3 h-5 w-5" />
      {children}
    </Link>
  );
};

interface AdminLayoutProps {
  children: ReactNode;
}

const AdminLayout = ({ children }: AdminLayoutProps) => {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (!user || !user.is_superuser) {
        router.push('/login');
      }
    }
  }, [user, loading, router]);

  if (loading || !user || !user.is_superuser) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-gray-600" />
        <p className="mt-3 text-gray-700">Carregando painel administrativo...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="w-64 bg-gray-800 text-white flex-shrink-0 hidden md:flex md:flex-col">
        <div className="p-5 text-2xl font-bold border-b border-gray-700 flex-shrink-0">
          <Link href="/admin/dashboard">Admin Panel</Link>
        </div>
        <nav className="p-4 space-y-2 flex-grow">
          <AdminNavItem href="/admin/dashboard" icon={LayoutDashboard}>
            Dashboard
          </AdminNavItem>
          <AdminNavItem href="/admin/categories" icon={FolderKanban}>
            Categorias
          </AdminNavItem>
          <AdminNavItem href="/admin/products" icon={Box}>
            Produtos
          </AdminNavItem>
          <AdminNavItem href="/admin/orders" icon={ShoppingBag}>
            Pedidos
          </AdminNavItem>
          <AdminNavItem href="/admin/users" icon={Users}>
            Usuários
          </AdminNavItem>
        </nav>
      </aside>

      <div className="flex-grow flex flex-col">
        <AdminNavbar />
        <main className="flex-grow p-6 md:p-8">{children}</main>
      </div>
    </div>
  );
};

export default AdminLayout;
