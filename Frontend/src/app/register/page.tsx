/**
 * @file Página de Registro de Novo Usuário.
 * @description Contém o formulário completo para que um novo usuário possa criar
 * uma conta, fornecendo dados de acesso, pessoais e de endereço. A validação
 * dos dados é feita utilizando Zod e react-hook-form.
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2 } from 'lucide-react';

import { useAuth } from '@/context/AuthContext';
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

const registerSchema = z.object({
  email: z.string().email({ message: 'Por favor, insira um e-mail válido.' }),
  password: z.string().min(6, { message: 'A senha deve ter pelo menos 6 caracteres.' }),
  full_name: z.string().min(3, { message: 'Nome completo é obrigatório.' }),
  cpf: z.string().min(11, { message: 'CPF inválido.' }),
  phone: z.string().min(10, { message: 'Telefone inválido.' }),
  address_street: z.string().min(3, { message: 'Endereço é obrigatório.' }),
  address_number: z.string().min(1, { message: 'Número é obrigatório.' }),
  address_complement: z.string().optional(),
  address_zip: z.string().min(8, { message: 'CEP inválido.' }),
  address_city: z.string().min(2, { message: 'Cidade é obrigatória.' }),
  address_state: z.string().length(2, { message: 'Use a sigla do estado (ex: SP).' }),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;

const RegisterPage = () => {
  const { register, loading, error } = useAuth();

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      full_name: '',
      cpf: '',
      phone: '',
      address_street: '',
      address_number: '',
      address_complement: '',
      address_zip: '',
      address_city: '',
      address_state: '',
    },
  });

  const onSubmit = (data: RegisterFormValues) => {
    register(data);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-2xl p-8 space-y-8 bg-white shadow-lg rounded-lg">
        <div>
          <h2 className="text-center text-3xl font-extrabold text-gray-900">Crie sua Conta</h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Preencha todos os campos para continuar.
          </p>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            <fieldset className="space-y-4">
              <legend className="font-semibold text-lg border-b pb-2 mb-4 w-full">
                Dados de Acesso
              </legend>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>E-mail</FormLabel>
                      <FormControl>
                        <Input placeholder="seu@email.com" {...field} autoComplete="email" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Senha</FormLabel>
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
              </div>
            </fieldset>

            <fieldset className="space-y-4">
              <legend className="font-semibold text-lg border-b pb-2 mb-4 w-full">
                Dados Pessoais
              </legend>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                <FormField
                  control={form.control}
                  name="full_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nome Completo</FormLabel>
                      <FormControl>
                        <Input placeholder="Seu nome" {...field} autoComplete="name" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="cpf"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>CPF</FormLabel>
                      <FormControl>
                        <Input placeholder="000.000.000-00" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="phone"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Telefone</FormLabel>
                      <FormControl>
                        <Input placeholder="(XX) XXXXX-XXXX" {...field} autoComplete="tel" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </fieldset>

            <fieldset className="space-y-4">
              <legend className="font-semibold text-lg border-b pb-2 mb-4 w-full">
                Endereço de Entrega
              </legend>
              <div className="grid grid-cols-6 gap-x-6 gap-y-4">
                <div className="col-span-6 sm:col-span-2">
                  <FormField
                    control={form.control}
                    name="address_zip"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>CEP</FormLabel>
                        <FormControl>
                          <Input placeholder="00000-000" {...field} autoComplete="postal-code" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
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
                          <Input
                            placeholder="Nome da sua rua"
                            {...field}
                            autoComplete="address-line1"
                          />
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
                        <FormLabel>Complemento (opcional)</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Apto, bloco, etc."
                            {...field}
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
                          <Input
                            placeholder="SP"
                            {...field}
                            autoComplete="address-level1"
                            maxLength={2}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>
            </fieldset>

            {error && (
              <p
                className="mt-4 text-sm font-semibold text-center text-red-600 bg-red-100 p-3 rounded-md"
                role="alert"
              >
                {error}
              </p>
            )}

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Registrando...
                </>
              ) : (
                'Criar minha conta'
              )}
            </Button>

            <div className="text-center mt-4">
              <Link href="/login" className="text-sm font-medium text-teal-600 hover:text-teal-500">
                Já tem uma conta? Faça login
              </Link>
            </div>
          </form>
        </Form>
      </div>
    </div>
  );
};

export default RegisterPage;
