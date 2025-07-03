/**
 * @file Página do Carrinho de Compras.
 * @description Exibe os itens do carrinho do usuário, permite a manipulação
 * de quantidades, aplicação de cupons e o início do processo de checkout.
 */

'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { X, Plus, Minus, Loader2, CreditCard, Ticket, Trash2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';

/**
 * Componente principal da Página do Carrinho.
 */
const CartPage = () => {
  const { user, cart, fetchCart, loading: authLoading } = useAuth();
  const router = useRouter();

  const [isUpdating, setIsUpdating] = useState(false);
  const [couponCode, setCouponCode] = useState('');
  const [couponError, setCouponError] = useState<string | null>(null);
  const [isCouponLoading, setIsCouponLoading] = useState(false);
  const [isCheckoutLoading, setIsCheckoutLoading] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login?redirect=/cart');
    }
  }, [user, authLoading, router]);

  const handleError = (error: unknown, defaultMessage: string) => {
    const message = error instanceof Error ? error.message : defaultMessage;
    console.error(defaultMessage, error);
    return message;
  };

  const handleUpdateQuantity = useCallback(
    async (productId: number, newQuantity: number) => {
      setIsUpdating(true);
      try {
        await api.updateCartItem(productId, newQuantity);
        await fetchCart();
      } catch (error) {
        alert(handleError(error, 'Erro ao atualizar item.'));
      } finally {
        setIsUpdating(false);
      }
    },
    [fetchCart],
  );

  const handleRemoveItem = useCallback(
    async (productId: number) => {
      if (!window.confirm('Tem certeza que deseja remover este item do carrinho?')) return;

      setIsUpdating(true);
      try {
        await api.removeCartItem(productId);
        await fetchCart();
      } catch (error) {
        alert(handleError(error, 'Erro ao remover item.'));
      } finally {
        setIsUpdating(false);
      }
    },
    [fetchCart],
  );

  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!couponCode) return;

    setIsCouponLoading(true);
    setCouponError(null);
    try {
      await api.applyCoupon(couponCode);
      setCouponCode('');
      await fetchCart();
    } catch (error) {
      setCouponError(handleError(error, 'Não foi possível aplicar o cupom.'));
    } finally {
      setIsCouponLoading(false);
    }
  };

  const handleRemoveCoupon = async () => {
    setIsCouponLoading(true);
    setCouponError(null);
    try {
      await api.removeCoupon();
      await fetchCart();
    } catch (error) {
      setCouponError(handleError(error, 'Erro ao remover cupom.'));
    } finally {
      setIsCouponLoading(false);
    }
  };

  const handleCheckout = async () => {
    setIsCheckoutLoading(true);
    try {
      const orderData = await api.createOrder();

      const stripeData = await api.createCheckoutSession(orderData.id);

      window.location.href = stripeData.checkout_url;
    } catch (error) {
      alert(
        handleError(
          error,
          'Não foi possível iniciar o checkout. Verifique os itens e tente novamente.',
        ),
      );
      setIsCheckoutLoading(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <Loader2 className="h-10 w-10 animate-spin text-gray-500" />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="text-center py-20 flex flex-col items-center">
        <h1 className="text-2xl font-bold text-gray-800">Seu carrinho está vazio.</h1>
        <Link
          href="/"
          className="text-white bg-black hover:bg-gray-800 font-semibold py-3 px-6 rounded-lg mt-6 inline-block"
        >
          Continue Comprando
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="container mx-auto px-4 py-8 md:py-12">
        <h1 className="text-3xl font-bold mb-8 text-gray-900">Seu Carrinho</h1>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          {/* Lista de Itens do Carrinho */}
          <ul className="lg:col-span-2 bg-white p-6 rounded-lg shadow-sm space-y-4">
            {cart.items.map((item) => (
              <li
                key={item.id}
                className="flex items-center space-x-4 py-4 border-b last:border-b-0"
              >
                <div className="relative h-24 w-24 rounded-md overflow-hidden flex-shrink-0 bg-gray-100">
                  {item.product.image_url && (
                    <Image
                      src={item.product.image_url}
                      alt={item.product.name}
                      fill
                      style={{ objectFit: 'cover' }}
                    />
                  )}
                </div>
                <div className="flex-grow">
                  <Link
                    href={`/product/${item.product.id}`}
                    className="font-semibold text-gray-800 hover:underline"
                  >
                    {item.product.name}
                  </Link>
                  <p className="text-sm text-gray-500 font-mono">
                    R$ {item.product.price.toFixed(2).replace('.', ',')}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleUpdateQuantity(item.product.id, item.quantity - 1)}
                    className="p-1 rounded-full text-gray-600 hover:bg-gray-200"
                    aria-label="Diminuir quantidade"
                  >
                    <Minus size={16} />
                  </button>
                  <span className="w-10 text-center font-semibold text-gray-800" aria-live="polite">
                    {item.quantity}
                  </span>
                  <button
                    onClick={() => handleUpdateQuantity(item.product.id, item.quantity + 1)}
                    className="p-1 rounded-full text-gray-600 hover:bg-gray-200"
                    aria-label="Aumentar quantidade"
                  >
                    <Plus size={16} />
                  </button>
                </div>
                <p className="font-semibold w-24 text-right text-gray-800 font-mono">
                  R$ {(item.product.price * item.quantity).toFixed(2).replace('.', ',')}
                </p>
                <button
                  onClick={() => handleRemoveItem(item.product.id)}
                  className="ml-4 text-gray-400 hover:text-red-500"
                  aria-label={`Remover ${item.product.name} do carrinho`}
                >
                  <X size={20} />
                </button>
              </li>
            ))}
          </ul>

          {/* Resumo e Checkout */}
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow-sm sticky top-28 space-y-4">
              <h2 className="text-xl font-bold border-b pb-4 text-gray-900">Resumo</h2>

              {/* Seção do Cupom */}
              <div>
                {!cart.coupon ? (
                  <form onSubmit={handleApplyCoupon} className="flex gap-2">
                    <input
                      type="text"
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                      placeholder="Código do Cupom"
                      className="w-full px-3 py-2 border rounded-md"
                      aria-label="Código do Cupom"
                    />
                    <button
                      type="submit"
                      className="bg-gray-200 text-gray-800 px-4 rounded-md hover:bg-gray-300 flex items-center justify-center"
                      disabled={isCouponLoading}
                      aria-label="Aplicar Cupom"
                    >
                      {isCouponLoading ? (
                        <Loader2 className="animate-spin h-5 w-5" />
                      ) : (
                        <Ticket size={20} />
                      )}
                    </button>
                  </form>
                ) : (
                  <div className="flex justify-between items-center bg-green-100 text-green-800 p-2 rounded-md">
                    <p className="text-sm font-semibold">
                      Cupom aplicado: <span className="font-mono">{cart.coupon.code}</span>
                    </p>
                    <button
                      onClick={handleRemoveCoupon}
                      disabled={isCouponLoading}
                      aria-label="Remover Cupom"
                    >
                      {isCouponLoading ? (
                        <Loader2 className="animate-spin h-4 w-4" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                )}
                {couponError && (
                  <p className="text-red-500 text-xs mt-1" role="alert">
                    {couponError}
                  </p>
                )}
              </div>

              {/* Detalhes de Preço */}
              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between text-gray-600">
                  <p>Subtotal</p>
                  <p className="font-mono">R$ {cart.subtotal.toFixed(2).replace('.', ',')}</p>
                </div>
                {cart.discount_amount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <p>Desconto ({cart.coupon?.code})</p>
                    <p className="font-mono">
                      - R$ {cart.discount_amount.toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                )}
                <div className="flex justify-between font-bold text-lg text-gray-900 pt-2 border-t">
                  <p>Total</p>
                  <p className="font-mono">R$ {cart.final_price.toFixed(2).replace('.', ',')}</p>
                </div>
              </div>

              <button
                onClick={handleCheckout}
                disabled={isCheckoutLoading || isUpdating}
                className="w-full bg-black text-white py-3 rounded-lg font-semibold hover:bg-gray-800 flex items-center justify-center disabled:bg-gray-500"
              >
                {isCheckoutLoading ? (
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                ) : (
                  <CreditCard className="mr-2 h-5 w-5" />
                )}
                {isCheckoutLoading ? 'Processando...' : 'Finalizar Compra'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartPage;
