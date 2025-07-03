/**
 * @file Layout Raiz da Aplicação.
 * @description Este componente é o principal layout que envolve todas as páginas
 * da aplicação. É responsável por definir a estrutura HTML base (<html>, <body>),
 * importar fontes globais, aplicar estilos globais e prover contextos, como
 * o de autenticação.
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import './globals.css';

import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { AuthProvider } from '@/context/AuthContext';

const inter = Inter({ subsets: ['latin'] });

/**
 * Metadados estáticos para SEO.
 * Define o título e a descrição padrão para as páginas da aplicação.
 * Páginas específicas podem sobrescrever ou estender estes metadados.
 */
export const metadata: Metadata = {
  title: 'E-Commerce',
  description: 'Um E-Commerce completo.',
  // TODO: Adicionar mais metadados para SEO, como 'keywords', 'author', 'opengraph', etc.
};

/**
 * Componente funcional do Layout Raiz.
 *
 * @param {object} props
 * @param {React.ReactNode} props.children
 * @returns {JSX.Element}
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-br" className="h-full">
      {/* 
        Aplica a classe da fonte otimizada e usa flexbox para garantir que o footer 
        permaneça na parte inferior da tela, mesmo em páginas com pouco conteúdo.
      */}
      <body className={`${inter.className} flex flex-col min-h-full`}>
        {/*
          O AuthProvider envolve toda a aplicação, disponibilizando o estado de 
          autenticação (usuário, carrinho) para qualquer componente que precise.
        */}
        <AuthProvider>
          <Header />
          <main className="flex-grow">{children}</main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
