/**
 * @file Contexto de Autenticação e Estado Global do Usuário.
 * @description Provê estado global para o usuário autenticado e seu carrinho,
 * bem como as funções para interagir com a API de autenticação.
 */

'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

import { Product } from '@/types';
import type { RegisterFormValues } from '@/app/register/page';
import type { Order } from '@/app/meus-pedidos/page';
import { api } from '@/lib/api';

export interface User {
  id: number;
  email: string;
  is_superuser: boolean;
  is_active: boolean;
  full_name: string;
  cpf: string;
  phone: string;
  address_street: string;
  address_number: string;
  address_complement: string | null;
  address_zip: string;
  address_city: string;
  address_state: string;
  orders: Order[];
}

export interface CartItem {
  id: number;
  quantity: number;
  product: Product;
}

export interface Coupon {
  id: number;
  code: string;
  discount_percent: number;
}

export interface Cart {
  id: number;
  items: CartItem[];
  subtotal: number;
  discount_amount: number;
  final_price: number;
  coupon: Coupon | null;
}

interface AuthContextType {
  user: User | null;
  cart: Cart | null;
  loading: boolean;
  error: string | null;
  fetchCart: () => Promise<void>;
  fetchUser: () => Promise<void>;
  login: (formData: FormData) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterFormValues) => Promise<void>;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const fetchCart = useCallback(async () => {
    try {
      const data = await api.getCart();
      setCart(data);
    } catch (e) {
      console.error('Falha ao buscar carrinho:', e);
      setCart(null);
    }
  }, []);

  const fetchUser = useCallback(async () => {
    const token = Cookies.get('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const userData = await api.getUserProfile();
      setUser(userData);

      if (!userData.is_superuser) {
        await fetchCart();
      }
    } catch (err) {
      console.error('Falha ao buscar usuário. Desconectando...', err);
      Cookies.remove('access_token');
      setUser(null);
      setCart(null);
    } finally {
      setLoading(false);
    }
  }, [fetchCart]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (formData: FormData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.login(formData);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Falha no login.');

      Cookies.set('access_token', data.access_token, {
        expires: 1,
        secure: process.env.NODE_ENV === 'production',
      });

      const userData = await api.getUserProfile();
      setUser(userData);
      if (!userData.is_superuser) await fetchCart();

      router.push(userData.is_superuser ? '/admin/dashboard' : '/');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Um erro inesperado ocorreu.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: RegisterFormValues) => {
    setLoading(true);
    setError(null);
    try {
      const registerResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/users/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData),
        },
      );

      const registerData = await registerResponse.json();
      if (!registerResponse.ok) {
        if (registerData.detail && Array.isArray(registerData.detail)) {
          const errorMessage = registerData.detail
            .map((err: { msg: string }) => err.msg)
            .join(', ');
          throw new Error(errorMessage);
        }
        throw new Error(registerData.detail || 'Falha ao tentar registrar.');
      }

      const loginFormData = new FormData();
      loginFormData.append('username', userData.email);
      loginFormData.append('password', userData.password);
      await login(loginFormData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Um erro inesperado ocorreu.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    Cookies.remove('access_token');
    setUser(null);
    setCart(null);
    router.push('/login');
  };

  const value = {
    user,
    cart,
    loading,
    error,
    setError,
    fetchCart,
    fetchUser,
    login,
    logout,
    register,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};
