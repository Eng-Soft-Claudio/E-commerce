/**
 * @file Componente de Cliente para Visualização de Produto.
 * @description Renderiza a interface da página de detalhes de um produto,
 * lidando com as interações do usuário, como adicionar o item ao carrinho.
 * Recebe os dados do produto como prop de um Server Component pai.
 */

'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Loader2, ShoppingCart, Image as ImageIcon, Info } from 'lucide-react';

import { Product } from '@/types';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';

interface ProductViewClientProps {
  product: Product;
}

export default function ProductViewClient({ product }: ProductViewClientProps) {
  const [isAdding, setIsAdding] = useState(false);

  const { user, fetchCart } = useAuth();
  const router = useRouter();

  /**
   * Manipula a ação de adicionar o produto ao carrinho.
   */
  const handleAddToCart = async () => {
    if (!user) {
      router.push(`/login?redirect=/product/${product.id}`);
      return;
    }
    if (product.stock <= 0) return;

    setIsAdding(true);
    try {
      await api.addItemToCart(product.id, 1);

      alert(`"${product.name}" foi adicionado ao seu carrinho!`);
      await fetchCart();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Falha ao adicionar o produto.';
      console.error(error);
      alert(`Erro: ${message}`);
    } finally {
      setIsAdding(false);
    }
  };

  const isOutOfStock = product.stock <= 0;

  return (
    <div className="bg-white">
      <div className="container mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-12 lg:gap-x-16">
          {/* Seção da Imagem do Produto */}
          <div className="relative aspect-square rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center">
            {product.image_url ? (
              <Image
                src={product.image_url}
                alt={product.name}
                fill
                className="object-contain object-center p-4"
                sizes="(max-width: 768px) 90vw, 45vw"
                priority
              />
            ) : (
              <div className="text-gray-400">
                <ImageIcon size={64} strokeWidth={1} />
                <p className="sr-only">Sem imagem disponível</p>
              </div>
            )}
          </div>

          {/* Seção de Informações e Ações */}
          <div className="flex flex-col">
            {/* Categoria */}
            {product.category && (
              <Link
                href={`/category/${product.category.id}`}
                className="text-sm font-medium text-teal-600 hover:text-teal-800"
              >
                {product.category.title}
              </Link>
            )}

            <h1 className="text-3xl lg:text-4xl font-bold tracking-tight text-gray-900 mt-2">
              {product.name}
            </h1>

            {/* Preço */}
            <div className="mt-4">
              <p className="text-3xl text-gray-800">
                R$ {product.price.toFixed(2).replace('.', ',')}
              </p>
            </div>

            {/* Descrição */}
            {product.description && (
              <div className="mt-8">
                <h3 className="text-base font-semibold text-gray-900">Descrição</h3>
                <div className="mt-2 text-base text-gray-600 space-y-4">
                  <p>{product.description}</p>
                </div>
              </div>
            )}

            <div className="mt-10 pt-6 border-t">
              {isOutOfStock && (
                <div className="mb-4 flex items-center gap-2 text-yellow-700 bg-yellow-50 p-3 rounded-md">
                  <Info size={20} />
                  <p className="text-sm font-semibold">
                    Este produto está indisponível no momento.
                  </p>
                </div>
              )}
              <button
                onClick={handleAddToCart}
                disabled={isAdding || isOutOfStock}
                className="flex w-full max-w-xs items-center justify-center rounded-md border border-transparent bg-black px-8 py-3 text-base font-medium text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isAdding ? (
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                ) : (
                  <ShoppingCart className="mr-2 h-5 w-5" />
                )}
                {isOutOfStock
                  ? 'Indisponível'
                  : isAdding
                    ? 'Adicionando...'
                    : 'Adicionar ao Carrinho'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
