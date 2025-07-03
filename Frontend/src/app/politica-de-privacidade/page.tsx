/**
 * @file Página de Política de Privacidade.
 * @description Detalha como os dados dos usuários são coletados, usados e protegidos.
 */

import React from 'react';
import type { Metadata } from 'next';

import StaticPageLayout from '@/components/layout/StaticPageLayout';

/**
 * Metadados da página para SEO.
 */
export const metadata: Metadata = {
  title: 'Política de Privacidade | E-Commerce Louva-Deus',
  description: 'Entenda como coletamos, usamos e protegemos seus dados pessoais em nosso site.',
};

/**
 * Componente da página de Política de Privacidade.
 */
const PoliticaDePrivacidadePage = () => {
  return (
    <StaticPageLayout title="Política de Privacidade">
      <p>
        <strong>Última atualização:</strong> {new Date().toLocaleDateString('pt-BR')}
      </p>

      <h2>1. Coleta de Informações</h2>
      <p>
        Coletamos informações que você nos fornece diretamente, como nome, e-mail, endereço e
        telefone, ao criar uma conta ou realizar um pedido. Também coletamos dados de transações
        relacionados às suas compras.
      </p>

      <h2>2. Uso das Informações</h2>
      <p>As informações coletadas são utilizadas para:</p>
      <ul>
        <li>Processar seus pedidos e gerenciar sua conta.</li>
        <li>Melhorar nosso site e a experiência de compra.</li>
        <li>Enviar comunicações promocionais, caso você opte por recebê-las.</li>
        <li>Cumprir obrigações legais e fiscais.</li>
      </ul>

      <h2>3. Compartilhamento de Informações</h2>
      <p>
        Não compartilhamos suas informações pessoais com terceiros, exceto quando necessário para a
        prestação de nossos serviços (ex: com transportadoras para entrega e com processadores de
        pagamento para transações financeiras) ou quando exigido por lei.
      </p>

      <h2>4. Segurança dos Dados</h2>
      <p>
        Implementamos medidas de segurança para proteger suas informações pessoais contra acesso,
        alteração, divulgação ou destruição não autorizada. No entanto, nenhum método de transmissão
        pela Internet é 100% seguro.
      </p>

      <h2>5. Seus Direitos</h2>
      <p>
        Você tem o direito de acessar, corrigir ou excluir suas informações pessoais a qualquer
        momento através da área Minha Conta ou entrando em contato com nosso suporte.
      </p>
    </StaticPageLayout>
  );
};

export default PoliticaDePrivacidadePage;
