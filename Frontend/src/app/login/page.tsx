/**
 * @file Página de Login de Usuário.
 * @description Fornece um formulário para que usuários existentes possam se
 * autenticar na aplicação. Utiliza o AuthContext para gerenciar o estado
 * de autenticação e feedback de erro/carregamento.
 */

'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Loader2 } from 'lucide-react';
import Link from 'next/link';

/**
 * Componente funcional que renderiza o formulário de login.
 * Controla o estado dos campos de e-mail e senha e dispara a função
 * de login provida pelo AuthContext.
 */
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const { login, loading, error } = useAuth();

  /**
   * Manipula o evento de submissão do formulário.
   * Previne o comportamento padrão, monta os dados em um FormData
   * e chama a função de login.
   * @param {React.FormEvent<HTMLFormElement>} event - O evento do formulário.
   */
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!email || !password) return;

    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    await login(formData);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="w-full max-w-sm px-8 py-8 bg-white shadow-lg rounded-lg">
        <h3 className="text-2xl font-bold text-center text-gray-800">Login na sua Conta</h3>
        <form onSubmit={handleSubmit} className="mt-6">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700" htmlFor="email">
                E-mail
              </label>
              <input
                type="email"
                placeholder="seu@email.com"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-black"
                autoComplete="email"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700" htmlFor="password">
                Senha
              </label>
              <input
                type="password"
                placeholder="Sua senha"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-black"
                autoComplete="current-password"
                required
              />
            </div>
          </div>

          {error && (
            <p className="mt-4 text-sm text-center text-red-600" role="alert">
              {error}
            </p>
          )}

          <div className="mt-6">
            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-2.5 text-white bg-black rounded-lg hover:bg-gray-800 disabled:bg-gray-400 flex justify-center items-center transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Entrando...
                </>
              ) : (
                'Entrar'
              )}
            </button>
          </div>

          <div className="mt-4 text-center">
            <Link href="/register" className="text-sm text-teal-600 hover:underline">
              Não tem uma conta? Crie uma agora.
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
