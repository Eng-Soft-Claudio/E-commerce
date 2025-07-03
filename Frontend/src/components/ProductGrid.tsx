/**
 * @file Componente reutilizável para exibir uma grade de produtos.
 * @description Renderiza uma grade responsiva de `ProductCard` ou uma
 * mensagem de "nenhum produto encontrado" se a lista estiver vazia.
 */

'use client';

import React from 'react';
import { PackageSearch } from 'lucide-react'; // Ícone para UX

import { Product } from '@/types';
import ProductCard from './ProductCard';

/**
 * Props para o componente ProductGrid.
 */
interface ProductGridProps {
  products: Product[];
  title?: string;
  emptyStateMessage?: string;
}

/**
 * Componente que renderiza uma grade de produtos. É projetado para ser
 * flexível, aceitando um título e uma mensagem customizada para estado vazio.
 */
const ProductGrid = ({
  products,
  title,
  emptyStateMessage = 'Nenhum produto encontrado que corresponda aos seus critérios.',
}: ProductGridProps) => {
  return (
    <section aria-labelledby={title ? 'product-grid-title' : undefined}>
      {title && (
        <h2
          id="product-grid-title"
          className="text-2xl font-bold tracking-tight text-gray-900 mb-8"
        >
          {title}
        </h2>
      )}

      {products.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center text-gray-500 bg-gray-50 rounded-lg">
          <PackageSearch className="h-12 w-12 text-gray-400" />
          <p className="mt-4 font-semibold text-lg">{emptyStateMessage}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-4 xl:gap-x-8">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </section>
  );
};

export default ProductGrid;