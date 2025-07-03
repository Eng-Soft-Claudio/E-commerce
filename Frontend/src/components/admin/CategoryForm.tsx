/**
 * @file Formulário reutilizável para criar e editar categorias.
 * @description Utiliza react-hook-form para gerenciamento de estado e Zod
 * para validação de schema, garantindo um formulário robusto e seguro.
 */

'use client';

import React, { useEffect } from 'react';
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

/**
 * Schema de validação Zod para os dados do formulário da categoria.
 */
const formSchema = z.object({
  title: z.string().min(2, { message: 'O título deve ter pelo menos 2 caracteres.' }),
  description: z.string().optional().nullable(),
});

export type CategoryFormValues = z.infer<typeof formSchema>;

interface CategoryFormProps {
  onSubmit: (values: CategoryFormValues) => void;
  initialData?: Partial<CategoryFormValues>;
  isLoading: boolean;
}

/**
 * Componente do formulário de categoria, que pode ser usado tanto para
 * criação quanto para edição.
 */
export const CategoryForm = ({ onSubmit, initialData, isLoading }: CategoryFormProps) => {
  const form = useForm<CategoryFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: initialData || { title: '', description: '' },
  });

  /**
   * Efeito para resetar o formulário quando `initialData` mudar.
   * Isso garante que, se o usuário fechar o modal de edição de um item e
   * abrir o de outro, os campos serão atualizados corretamente.
   */
  useEffect(() => {
    form.reset(initialData || { title: '', description: '' });
  }, [initialData, form]);

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="space-y-6">
        <fieldset disabled={isLoading} className="space-y-4">
          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Título da Categoria</FormLabel>
                <FormControl>
                  <Input
                    placeholder="Ex: Terços, Imagens, Livros"
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
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Descrição (opcional)</FormLabel>
                <FormControl>
                  <Input
                    placeholder="Uma breve descrição sobre a categoria"
                    {...field}
                    value={field.value || ''}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </fieldset>

        <Button type="submit" disabled={isLoading} className="w-full">
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Salvando...
            </>
          ) : (
            'Salvar Categoria'
          )}
        </Button>
      </form>
    </Form>
  );
};
