/**
 * @file Serviço de API centralizado.
 * @description Encapsula toda a lógica de comunicação com a API backend,
 * gerenciando URLs, autenticação e tratamento básico de respostas e erros.
 */

import Cookies from 'js-cookie';
import { ProfileFormValues } from '@/components/user/UserProfileForm';
import { PasswordFormValues } from '@/components/user/ChangePasswordForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type FetchOptions = RequestInit & {
  requiresAuth?: boolean;
};

async function apiFetch(endpoint: string, options: FetchOptions = {}) {
  const url = `${API_URL}${endpoint}`;
  const token = Cookies.get('access_token');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (options.requiresAuth && token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, { ...options, headers });

    if (response.status === 204) {
      return { success: true };
    }

    const data = await response.json().catch(() => {
      throw new Error(`Resposta inválida do servidor com status: ${response.status}`);
    });

    if (!response.ok) {
      throw new Error(data.detail || `Erro na API: ${response.statusText}`);
    }

    return data;
  } catch (error) {
    console.error(`Erro na chamada da API para [${endpoint}]:`, error);
    throw error;
  }
}

export const api = {
  login: (formData: FormData) => {
    return fetch(`${API_URL}/auth/token`, {
      method: 'POST',
      body: formData,
    });
  },
  getUserProfile: () => apiFetch('/auth/users/me/', { requiresAuth: true }),
  updatePassword: (data: PasswordFormValues) =>
    apiFetch('/auth/users/me/password', {
      method: 'PUT',
      body: JSON.stringify(data),
      requiresAuth: true,
    }),
  updateProfile: (data: ProfileFormValues) =>
    apiFetch('/auth/users/me/', {
      method: 'PUT',
      body: JSON.stringify(data),
      requiresAuth: true,
    }),
  getCart: () => apiFetch('/cart/', { requiresAuth: true }),
  addItemToCart: (productId: number, quantity: number) =>
    apiFetch('/cart/items/', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity }),
      requiresAuth: true,
    }),
  updateCartItem: (productId: number, quantity: number) =>
    apiFetch(`/cart/items/${productId}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity }),
      requiresAuth: true,
    }),
  removeCartItem: (productId: number) =>
    apiFetch(`/cart/items/${productId}`, {
      method: 'DELETE',
      requiresAuth: true,
    }),
  applyCoupon: (code: string) =>
    apiFetch('/cart/apply-coupon', {
      method: 'POST',
      body: JSON.stringify({ code }),
      requiresAuth: true,
    }),
  removeCoupon: () =>
    apiFetch('/cart/apply-coupon', {
      method: 'DELETE',
      requiresAuth: true,
    }),

  getOrders: () => apiFetch('/orders/', { requiresAuth: true }),
  createOrder: () => apiFetch('/orders/', { method: 'POST', requiresAuth: true }),
  createCheckoutSession: (orderId: number) =>
    apiFetch(`/payments/create-checkout-session/${orderId}`, {
      method: 'POST',
      requiresAuth: true,
    }),
};
