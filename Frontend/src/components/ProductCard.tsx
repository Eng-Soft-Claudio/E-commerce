/**
 * @file Componente Card de Produto.
 * @description Exibe uma visualização compacta de um produto, incluindo imagem,
 * nome, preço e um botão para adicionar ao carrinho.
 */

'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Loader2, ShoppingCart } from 'lucide-react';

import { Product } from '@/types';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';

interface ProductCardProps {
  product: Product;
}

const ProductCard = ({ product }: ProductCardProps) => {
  const { user, fetchCart } = useAuth();
  const router = useRouter();
  const [isAdding, setIsAdding] = useState(false);

  /**
   * Manipula o clique no botão "Adicionar ao Carrinho".
   * Redireciona para o login se o usuário não estiver autenticado.
   * Caso contrário, adiciona o item ao carrinho via API e atualiza o estado global.
   */
  const handleAddToCart = async () => {
    if (!user) {
      router.push('/login');
      return;
    }

    setIsAdding(true);
    try {
      await api.addItemToCart(product.id, 1);

      alert(`"${product.name}" foi adicionado ao seu carrinho!`);

      await fetchCart();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Não foi possível adicionar o item ao carrinho.';
      console.error('Erro ao adicionar ao carrinho:', error);
      alert(`Erro: ${message}`);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="group relative border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-lg transition-shadow duration-300 flex flex-col justify-between bg-white">
      <Link href={`/product/${product.id}`} passHref aria-label={`Ver detalhes de ${product.name}`}>
        <div>
          <div className="relative aspect-w-1 aspect-h-1 w-full bg-gray-100 h-64 md:h-72">
            {product.image_url ? (
              <Image
                src={product.image_url}
                alt={product.name}
                fill
                className="object-contain object-center p-4 group-hover:opacity-80 transition-opacity"
                sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gray-200">
                <span className="text-gray-400">Sem Imagem</span>
              </div>
            )}
          </div>
          <div className="p-4">
            <h3 className="text-sm text-gray-700 truncate" title={product.name}>
              {product.name}
            </h3>
            <p className="mt-1 text-lg font-medium text-gray-900">
              R$ {product.price.toFixed(2).replace('.', ',')}
            </p>
          </div>
        </div>
      </Link>

      <div className="p-4 pt-0 mt-auto">
        <button
          onClick={handleAddToCart}
          disabled={isAdding || product.stock === 0}
          className="w-full bg-black text-white py-2 px-4 rounded-md hover:bg-gray-800 transition-colors flex items-center justify-center disabled:bg-gray-400 disabled:cursor-not-allowed"
          aria-label={`Adicionar ${product.name} ao carrinho`}
        >
          {isAdding ? (
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          ) : (
            <ShoppingCart className="mr-2 h-5 w-5" />
          )}
          {product.stock === 0 ? 'Indisponível' : isAdding ? 'Adicionando...' : 'Adicionar'}
        </button>
      </div>
    </div>
  );
};

export default ProductCard;
