/**
 * @file Página de Detalhe de um Produto específico.
 * @description Este é um Componente de Servidor (Server Component) responsável
 * por buscar os dados de um produto específico com base no ID da URL,
 * gerar metadados para SEO e, em seguida, passar os dados para um
 * componente de cliente para renderização e interatividade.
 */

import React from 'react';
import { notFound } from 'next/navigation';

import { Product } from '@/types';
import ProductViewClient from '@/components/ProductViewClient';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ProductPageProps {
  params: {
    id: string;
  };
}

/**
 * Busca os dados de um único produto no servidor.
 * Esta função é executada no servidor durante a renderização da página.
 * @param {string} productId
 * @returns {Promise<Product | null>}
 */
async function getProduct(productId: string): Promise<Product | null> {
  try {
    const res = await fetch(`${API_URL}/products/${productId}`, {
      cache: 'no-store',
    });

    if (res.status === 404) {
      return null;
    }
    if (!res.ok) {
      throw new Error('Falha ao buscar dados do produto do servidor');
    }
    return res.json();
  } catch (error) {
    console.error(`Erro na API ao buscar produto [ID: ${productId}]:`, error);
    return null;
  }
}

/**
 * Gera metadados dinâmicos (título e descrição) para a página do produto,
 * otimizando a página para mecanismos de busca (SEO).
 */
export async function generateMetadata({ params }: ProductPageProps) {
  const product = await getProduct(params.id);

  if (!product) {
    return {
      title: 'Produto não encontrado',
    };
  }
  return {
    title: `${product.name} | E-Commerce`,
    description: product.description || `Confira os detalhes e compre ${product.name}`,
  };
}

export default async function ProductDetailPage({ params }: ProductPageProps) {
  const product = await getProduct(params.id);

  if (!product) {
    notFound();
  }

  return <ProductViewClient product={product} />;
}
