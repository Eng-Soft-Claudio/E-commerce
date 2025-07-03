/**
 * @file Formulário para criação e edição de produtos.
 * @description Contém o schema de validação Zod e a estrutura do formulário reutilizável
 * para gerenciar os dados de um produto, incluindo detalhes logísticos.
 */

'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Product } from '@/types';

const formSchema = z.object({
  name: z.string().min(3, 'O nome deve ter pelo menos 3 caracteres.'),
  sku: z.string().min(3, 'O SKU deve ter pelo menos 3 caracteres.'),
  price: z.coerce.number().positive('O preço deve ser um número positivo.'),
  stock: z.coerce.number().int().min(0, 'O estoque não pode ser negativo.'),
  description: z.string().optional().nullable(),
  image_url: z.string().url('Deve ser uma URL válida.').optional().or(z.literal('')),
  category_id: z.coerce
    .number({ invalid_type_error: 'Selecione uma categoria válida.' })
    .int()
    .positive('Selecione uma categoria.'),
  weight_kg: z.coerce.number().positive('O peso deve ser maior que zero.'),
  height_cm: z.coerce.number().positive('A altura deve ser maior que zero.'),
  width_cm: z.coerce.number().positive('A largura deve ser maior que zero.'),
  length_cm: z.coerce.number().positive('O comprimento deve ser maior que zero.'),
});

export type ProductFormValues = z.infer<typeof formSchema>;

interface ProductFormProps {
  onSubmit: (values: ProductFormValues) => void;
  initialData?: Partial<Product>;
  categories: { id: number; title: string }[];
  isLoading: boolean;
}

export const ProductForm = ({ onSubmit, initialData, categories, isLoading }: ProductFormProps) => {
  const form = useForm<ProductFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: initialData
      ? {
          ...initialData,
          category_id: initialData.category?.id,
          image_url: initialData.image_url || '',
          description: initialData.description || '',
        }
      : {
          name: '',
          sku: '',
          price: 0,
          stock: 0,
          description: '',
          image_url: '',
          category_id: undefined,
          weight_kg: 0,
          height_cm: 0,
          width_cm: 0,
          length_cm: 0,
        },
  });

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-6 max-h-[70vh] overflow-y-auto pr-4"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nome do Produto</FormLabel>
                <FormControl>
                  <Input placeholder="Ex: Terço de Madeira" {...field} value={field.value || ''} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="sku"
            render={({ field }) => (
              <FormItem>
                <FormLabel>SKU</FormLabel>
                <FormControl>
                  <Input placeholder="Ex: TDM-001" {...field} value={field.value || ''} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            control={form.control}
            name="price"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Preço (R$)</FormLabel>
                <FormControl>
                  <Input type="number" step="0.01" placeholder="29.90" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="stock"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Estoque</FormLabel>
                <FormControl>
                  <Input type="number" step="1" placeholder="100" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="category_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Categoria</FormLabel>
              <select
                {...field}
                className="w-full h-10 px-3 border bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">Selecione uma categoria...</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </select>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Descrição</FormLabel>
              <FormControl>
                <Input
                  placeholder="Descrição detalhada do produto (opcional)"
                  {...field}
                  value={field.value || ''}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="image_url"
          render={({ field }) => (
            <FormItem>
              <FormLabel>URL da Imagem</FormLabel>
              <FormControl>
                <Input
                  placeholder="https://exemplo.com/imagem.jpg"
                  {...field}
                  value={field.value || ''}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div>
          <h3 className="text-lg font-medium mb-2 border-t pt-4">Dados de Logística</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Esses dados são essenciais para o cálculo do frete.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <FormField
              control={form.control}
              name="weight_kg"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Peso (Kg)</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.01" placeholder="0.5" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="height_cm"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Altura (cm)</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.1" placeholder="10" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="width_cm"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Largura (cm)</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.1" placeholder="15" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="length_cm"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Comprimento (cm)</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.1" placeholder="20" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </div>

        <Button type="submit" disabled={isLoading} className="w-full">
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Salvando...
            </>
          ) : (
            'Salvar Produto'
          )}
        </Button>
      </form>
    </Form>
  );
};
