/**
 * @file Página Inicial (Home) da Aplicação.
 * @description Este é o principal Server Component da aplicação, responsável por
 * buscar os dados iniciais de produtos e categorias para exibir na vitrine principal.
 */

import React from 'react';

import HeroCarousel from '@/components/HeroCarousel';
import ProductGrid from '@/components/ProductGrid';
import FeaturedCategories from '@/components/FeaturedCategories';
import { Product } from '@/types';
import { AlertCircle } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Category {
  id: number;
  title: string;
}

/**
 * Busca todos os produtos para a vitrine principal.
 * @returns Promise com um array de produtos ou nulo em caso de erro.
 */
async function getProducts(): Promise<Product[] | null> {
  try {
    const res = await fetch(`${API_URL}/products/`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Falha ao buscar produtos da API.');
    return res.json();
  } catch (error) {
    console.error('Erro em getProducts:', error);
    return null;
  }
}

/**
 * Busca todas as categorias para a seção de destaque.
 * @returns Promise com um array de categorias ou nulo em caso de erro.
 */
async function getCategories(): Promise<Category[] | null> {
  try {
    const res = await fetch(`${API_URL}/categories/`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Falha ao buscar categorias da API.');
    return res.json();
  } catch (error) {
    console.error('Erro em getCategories:', error);
    return null;
  }
}

export default async function Home() {
  const [productsData, categoriesData] = await Promise.all([getProducts(), getCategories()]);

  const products = productsData ?? [];
  const categories = categoriesData ?? [];

  const fetchError = !productsData || !categoriesData;

  return (
    <main className="flex flex-col items-center w-full">
      <HeroCarousel />
      <FeaturedCategories categories={categories} />

      <div className="container mx-auto px-4 py-12">
        {/* 
          Se houve erro na busca, exibe uma mensagem.
          Caso contrário, renderiza a grade de produtos.
        */}
        {fetchError ? (
          <div className="text-center py-10 bg-red-50 text-red-700 rounded-lg" role="alert">
            <AlertCircle className="mx-auto h-12 w-12" />
            <h3 className="mt-4 text-xl font-semibold">Ocorreu um erro</h3>
            <p className="mt-2">
              Não foi possível carregar os produtos. Tente novamente mais tarde.
            </p>
          </div>
        ) : (
          <ProductGrid
            title="PRODUTOS EM DESTAQUE"
            products={products}
            emptyStateMessage="Nenhum produto em destaque no momento."
          />
        )}
      </div>
    </main>
  );
}
