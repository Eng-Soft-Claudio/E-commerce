/**
 * @file Formulário reutilizável para o usuário alterar sua própria senha.
 * @description Este componente encapsula a lógica de validação para a
 * alteração de senha, garantindo que o usuário forneça a senha atual e que
 * a nova senha seja confirmada corretamente.
 */

'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2 } from 'lucide-react';

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

/**
 * Define o schema para a validação do formulário de alteração de senha.
 * - `current_password`: Deve ser fornecida.
 * - `new_password`: Mínimo de 6 caracteres.
 * - `refine`: Garante que o campo de confirmação da nova senha seja igual à nova senha.
 */
const passwordSchema = z
  .object({
    current_password: z.string().min(1, { message: 'A senha atual é obrigatória.' }),
    new_password: z.string().min(6, { message: 'A nova senha deve ter pelo menos 6 caracteres.' }),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'As novas senhas não coincidem.',
    path: ['confirm_password'],
  });

export type PasswordFormValues = z.infer<typeof passwordSchema>;

interface ChangePasswordFormProps {
  onSubmit: (data: PasswordFormValues) => void;
  isLoading: boolean;
}

/**
 * Componente do formulário de alteração de senha.
 */
export const ChangePasswordForm = ({ onSubmit, isLoading }: ChangePasswordFormProps) => {
  const form = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="space-y-6">
        <fieldset disabled={isLoading} className="space-y-4">
          <FormField
            control={form.control}
            name="current_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Senha Atual</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder="Sua senha atual"
                    {...field}
                    autoComplete="current-password"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="new_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nova Senha</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder="Mínimo de 6 caracteres"
                    {...field}
                    autoComplete="new-password"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="confirm_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirme a Nova Senha</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder="Repita a nova senha"
                    {...field}
                    autoComplete="new-password"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </fieldset>

        <Button type="submit" disabled={isLoading} className="w-full mt-6">
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Atualizando...
            </>
          ) : (
            'Alterar Senha'
          )}
        </Button>
      </form>
    </Form>
  );
};
