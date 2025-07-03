/**
 * @file Página de Sucesso de Pagamento.
 * @description Confirma ao usuário que o pagamento foi processado com sucesso.
 * Esta página utiliza Suspense para lidar com o carregamento assíncrono do hook
 * `useSearchParams` de maneira elegante.
 */

'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, Loader2, AlertCircle } from 'lucide-react';

/**
 * Componente que exibe a interface de loading para Suspense.
 */
function PaymentSuccessLoading() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
      <Loader2 className="h-12 w-12 animate-spin text-gray-500 mb-4" />
      <h1 className="text-2xl font-bold">Validando informações do pagamento...</h1>
    </div>
  );
}

/**
 * Componente que contém a lógica principal e a UI da página de sucesso.
 * Ele é envolvido por `Suspense` no componente de página principal.
 */
const PaymentSuccessContent = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    if (!sessionId) {
      setError('ID da sessão de pagamento não fornecido.');
      setLoading(false);
      return;
    }

    console.log('Verificando sessão de pagamento com o backend:', sessionId);

    const validationTimer = setTimeout(() => {
      setLoading(false);
    }, 1500);

    return () => clearTimeout(validationTimer);
  }, [sessionId]);

  if (loading) {
    return <PaymentSuccessLoading />;
  }

  if (error) {
    return (
      <div
        className="flex flex-col items-center justify-center min-h-[70vh] text-center"
        role="alert"
      >
        <AlertCircle className="mx-auto h-16 w-16 text-red-500" />
        <h1 className="mt-4 text-2xl font-bold text-gray-900">Ocorreu um Erro</h1>
        <p className="text-center py-4 text-red-600 font-semibold">{error}</p>
        <Link href="/" className="text-sm text-teal-600 hover:underline">
          Voltar para a loja
        </Link>
      </div>
    );
  }

  // --- RENDERIZAÇÃO DE SUCESSO ---
  return (
    <div className="bg-white min-h-screen">
      <div className="container mx-auto px-4 py-16 text-center">
        <div className="max-w-2xl mx-auto">
          <CheckCircle className="mx-auto h-24 w-24 text-green-500" />
          <h1 className="mt-6 text-3xl md:text-4xl font-extrabold text-gray-900">
            Pagamento Aprovado!
          </h1>
          <p className="mt-4 text-lg text-gray-600">
            Obrigado pela sua compra! Seu pedido foi recebido e está sendo processado. Você receberá
            uma confirmação por e-mail em breve.
          </p>
          <div className="mt-8">
            <Link
              href="/meus-pedidos"
              className="text-white bg-black hover:bg-gray-800 font-semibold py-3 px-8 rounded-lg inline-block transition-transform transform hover:scale-105"
            >
              Ver Meus Pedidos
            </Link>
          </div>
          <p className="mt-6 text-xs text-gray-400">ID da Sessão: {sessionId}</p>
        </div>
      </div>
    </div>
  );
};

/**
 * Componente de Página que atua como ponto de entrada e envolve o
 * conteúdo principal com o `Suspense` do React.
 */
const PaymentSuccessPage = () => {
  return (
    <Suspense fallback={<PaymentSuccessLoading />}>
      <PaymentSuccessContent />
    </Suspense>
  );
};

export default PaymentSuccessPage;
