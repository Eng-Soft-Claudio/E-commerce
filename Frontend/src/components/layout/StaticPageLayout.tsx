/**
 * @file Layout reutilizável para páginas de conteúdo estático.
 * @description Provê uma estrutura visual consistente para páginas institucionais,
 * como "Quem Somos", "Política de Privacidade", etc.
 */

import React from 'react';

interface StaticPageLayoutProps {
  title: string;
  children: React.ReactNode;
}

/**
 * Componente que define o container, o título e a área de conteúdo
 * estilizada para páginas estáticas.
 */
const StaticPageLayout = ({ title, children }: StaticPageLayoutProps) => {
  return (
    <div className="bg-gray-50 py-16 sm:py-24">
      <div className="container mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <header>
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl text-center">
            {title}
          </h1>
        </header>

        <main className="mt-12">
          {/* 
            A classe `prose` do plugin @tailwindcss/typography aplica automaticamente
            estilos de alta qualidade a parágrafos, listas, títulos, etc.
            É ideal para conteúdo gerado a partir de um CMS ou Markdown.
          */}
          <div className="prose prose-lg max-w-none text-gray-700">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default StaticPageLayout;