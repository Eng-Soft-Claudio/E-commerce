/**
 * @file Formulário reutilizável para o usuário visualizar e editar seu perfil.
 * @description Permite a edição de campos específicos do perfil do usuário,
 * enquanto exibe outros como somente leitura por motivos de segurança e integridade.
 */

'use client';

import React, { useEffect } from 'react';
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
import { Label } from '@/components/ui/label';
import { User } from '@/context/AuthContext';
import { formatCPF, formatCEP, formatPhone } from '@/lib/utils';

// --- SCHEMA DE VALIDAÇÃO (ZOD) ---

/**
 * Define as regras de validação para os campos editáveis do perfil.
 * Os campos são opcionais, permitindo atualizações parciais.
 */
const profileSchema = z.object({
  full_name: z.string().min(3, 'Nome completo é obrigatório.').optional(),
  phone: z.string().min(10, 'Telefone inválido.').optional(), 
  address_street: z.string().min(3, 'Endereço é obrigatório.').optional(),
  address_number: z.string().min(1, 'Número é obrigatório.').optional(),
  address_complement: z.string().optional().nullable(),
  address_zip: z.string().min(8, 'CEP inválido.').optional(), 
  address_city: z.string().min(2, 'Cidade é obrigatória.').optional(),
  address_state: z.string().length(2, 'Use a sigla do estado (ex: SP).').optional(),
});

export type ProfileFormValues = z.infer<typeof profileSchema>;


interface UserProfileFormProps {
  user: User;
  onSubmit: (data: ProfileFormValues) => void;
  isLoading: boolean;
}


export const UserProfileForm = ({ user, onSubmit, isLoading }: UserProfileFormProps) => {
  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user.full_name || '',
      phone: user.phone || '',
      address_street: user.address_street || '',
      address_number: user.address_number || '',
      address_complement: user.address_complement || '',
      address_zip: user.address_zip || '',
      address_city: user.address_city || '',
      address_state: user.address_state || '',
    },
  });

  useEffect(() => {
    form.reset(user);
  }, [user, form]);

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8" noValidate>
        <fieldset disabled={isLoading} className="space-y-4">
          <legend className="font-semibold text-lg border-b pb-2 mb-4 w-full">
            Dados Pessoais
          </legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome Completo</FormLabel>
                  <FormControl>
                    <Input {...field} autoComplete="name" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="space-y-2">
              <Label>Telefone</Label>
              <Input
                value={formatPhone(user.phone)}
                disabled
                className="bg-gray-100 cursor-not-allowed"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>E-mail</Label>
            <Input value={user.email} disabled className="bg-gray-100 cursor-not-allowed" />
          </div>
          <div className="space-y-2">
            <Label>CPF</Label>
            <Input
              value={formatCPF(user.cpf)}
              disabled
              className="bg-gray-100 cursor-not-allowed"
            />
          </div>
        </fieldset>

        <fieldset disabled={isLoading} className="space-y-4">
          <legend className="font-semibold text-lg border-b pb-2 mb-4 w-full">Endereço</legend>
          <div className="grid grid-cols-6 gap-4">
            <div className="col-span-6 sm:col-span-2 space-y-2">
              <Label>CEP</Label>
              <Input
                value={formatCEP(user.address_zip)}
                disabled
                className="bg-gray-100 cursor-not-allowed"
              />
            </div>
            <div className="col-span-6 sm:col-span-4">
              <FormField
                control={form.control}
                name="address_street"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Rua / Avenida</FormLabel>
                    <FormControl>
                      <Input {...field} autoComplete="address-line1" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="col-span-6 sm:col-span-2">
              <FormField
                control={form.control}
                name="address_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Número</FormLabel>
                    <FormControl>
                      <Input {...field} autoComplete="address-line2" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="col-span-6 sm:col-span-4">
              <FormField
                control={form.control}
                name="address_complement"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Complemento</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Opcional"
                        {...field}
                        value={field.value || ''}
                        autoComplete="address-line3"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="col-span-6 sm:col-span-4">
              <FormField
                control={form.control}
                name="address_city"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cidade</FormLabel>
                    <FormControl>
                      <Input {...field} autoComplete="address-level2" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="col-span-6 sm:col-span-2">
              <FormField
                control={form.control}
                name="address_state"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Estado (UF)</FormLabel>
                    <FormControl>
                      <Input {...field} maxLength={2} autoComplete="address-level1" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </div>
        </fieldset>

        <p className="text-xs text-gray-500 pt-4 border-t">
          <strong>Atenção:</strong> Para alterar campos críticos como CPF, CEP ou Telefone, por
          favor, entre em contato com nosso suporte.
        </p>

        <Button type="submit" disabled={isLoading} className="w-full mt-6">
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Atualizando...
            </>
          ) : (
            'Salvar Alterações'
          )}
        </Button>
      </form>
    </Form>
  );
};
