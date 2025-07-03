/**
 * @file Página de exibição de produtos de uma categoria específica.
 * @description Este é um Componente de Servidor (Server Component) que busca
 * os dados da categoria e seus produtos diretamente no servidor antes de renderizar a página.
 */

import React from 'react';
import { notFound } from 'next/navigation';

import ProductGrid from '@/components/ProductGrid';
import { Product } from '@/types';
import { PackageSearch } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Category {
  id: number;
  title: string;
  description?: string | null;
}

interface CategoryPageProps {
  params: {
    id: string;
  };
}

async function getCategoryDetails(categoryId: string): Promise<Category | null> {
  try {
    const res = await fetch(`${API_URL}/categories/${categoryId}`, {
      cache: 'no-store',
    });
    if (!res.ok) {
      if (res.status === 404) return null;
      throw new Error(`Falha na API ao buscar categoria: ${res.statusText}`);
    }
    return res.json();
  } catch (error) {
    console.error('Erro em getCategoryDetails:', error);
    return null;
  }
}

async function getProductsByCategory(categoryId: string): Promise<Product[]> {
  try {
    const res = await fetch(`${API_URL}/products/?category_id=${categoryId}`, {
      cache: 'no-store',
    });
    if (!res.ok) return [];
    return res.json();
  } catch (error) {
    console.error('Erro ao buscar produtos da categoria:', error);
    return [];
  }
}

export async function generateMetadata({ params }: CategoryPageProps) {
  const category = await getCategoryDetails(params.id);
  if (!category) {
    return { title: 'Categoria não encontrada' };
  }
  return {
    title: `${category.title} - E-Commerce`,
    description:
      category.description || `Confira todos os produtos da categoria ${category.title}.`,
  };
}

export default async function CategoryPage({ params }: CategoryPageProps) {
  const [category, products] = await Promise.all([
    getCategoryDetails(params.id),
    getProductsByCategory(params.id),
  ]);

  if (!category) {
    notFound();
  }

  return (
    <div className="bg-white">
      <div className="container mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200 pb-6 mb-8">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900">{category.title}</h1>
          {category.description && (
            <p className="mt-4 text-base text-gray-500 text-justify">{category.description}</p>
          )}
        </div>

        {products.length > 0 ? (
          <ProductGrid products={products} />
        ) : (
          <div className="text-center py-16">
            <PackageSearch className="mx-auto h-16 w-16 text-gray-400" />
            <h2 className="mt-4 text-xl font-semibold text-gray-700">Nenhum produto encontrado</h2>
            <p className="mt-2 text-gray-500">
              Ainda não há produtos disponíveis nesta categoria. Volte em breve!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
