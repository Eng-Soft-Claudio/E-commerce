/**
 * @file Página de Resultados de Busca.
 * @description Exibe produtos que correspondem a um termo de busca fornecido
 * pelo usuário via parâmetro de URL (`?q=...`). Este arquivo demonstra o uso
 * de `Suspense` para uma experiência de carregamento otimizada.
 */

import React, { Suspense } from 'react';
import { Loader2, PackageSearch } from 'lucide-react';

import ProductGrid from '@/components/ProductGrid';
import { Product } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SearchPageProps {
  searchParams: {
    q?: string;
  };
}

/**
 * Busca produtos na API com base em uma query, executado no servidor.
 * @param query - O termo de busca.
 * @returns Uma Promise com um array de produtos.
 */
async function searchProducts(query: string): Promise<Product[]> {
  if (!query.trim()) {
    return [];
  }

  try {
    const res = await fetch(`${API_URL}/products/?q=${encodeURIComponent(query)}`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      console.error(`Falha na API de busca, status: ${res.status}`);
      return [];
    }
    return res.json();
  } catch (error) {
    console.error('Erro de rede ao buscar produtos:', error);
    return [];
  }
}

/**
 * Componente que renderiza a grade de resultados após a busca.
 * Por ser assíncrono, ele pode ser envolvido por `Suspense`.
 */
async function SearchResults({ query }: { query: string }) {
  const products = await searchProducts(query);
  const hasResults = products.length > 0;

  const resultText = hasResults
    ? `${products.length} resultado(s) encontrado(s) para "${query}"`
    : `Nenhum resultado encontrado para "${query}".`;

  return (
    <div className="bg-white">
      <div className="container mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200 pb-6 mb-8">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-gray-900">
            Resultados da Busca
          </h1>
          {query && <p className="mt-4 text-base text-gray-600">{resultText}</p>}
        </div>

        {hasResults ? (
          <ProductGrid products={products} />
        ) : (
          <div className="text-center py-16 flex flex-col items-center">
            <PackageSearch className="h-16 w-16 text-gray-400" />
            <p className="mt-4 text-lg text-gray-600">
              Tente usar termos de busca diferentes ou mais gerais.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Componente de fallback exibido pelo `Suspense` enquanto os dados estão sendo carregados.
 */
function SearchLoading() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh]" aria-live="polite">
      <Loader2 className="h-10 w-10 animate-spin text-gray-500" />
      <p className="mt-4 text-lg text-gray-600">Buscando produtos...</p>
    </div>
  );
}

/**
 * O componente de página exportado, que orquestra a renderização.
 * Ele extrai a query da URL e usa Suspense para gerenciar o estado de carregamento.
 */
export default function SearchPage({ searchParams }: SearchPageProps) {
  const query = searchParams.q || '';

  return (
    <Suspense key={query} fallback={<SearchLoading />}>
      <SearchResults query={query} />
    </Suspense>
  );
}
