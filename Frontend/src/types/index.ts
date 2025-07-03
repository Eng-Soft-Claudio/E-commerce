// src/types/index.ts

/**
 * Interface que representa a estrutura de um Produto como recebido da API.
 * Inclui dados básicos, categoria associada, e informações de logística
 * para cálculo de frete.
 */
export interface Product {
  id: number;
  sku: string;
  name: string;
  image_url: string | null;
  price: number;
  stock: number;
  description: string | null;
  category: {
    id: number;
    title: string;
    description?: string | null;
  };
  weight_kg: number;
  height_cm: number;
  width_cm: number;
  length_cm: number;
}
