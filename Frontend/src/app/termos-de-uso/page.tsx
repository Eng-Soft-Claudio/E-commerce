/**
 * @file Página de Termos de Uso.
 * @description Apresenta as regras e condições para a utilização do site e seus serviços.
 */

import React from 'react';
import type { Metadata } from 'next';

import StaticPageLayout from '@/components/layout/StaticPageLayout';

/**
 * Metadados da página para SEO.
 */
export const metadata: Metadata = {
  title: 'Termos de Uso | E-Commerce Louva-Deus',
  description: 'Leia os termos e condições que regem o uso do nosso site e serviços.',
};

/**
 * Componente da página de Termos de Uso.
 */
const TermosDeUsoPage = () => {
  return (
    <StaticPageLayout title="Termos de Uso">
        <h2>1. Aceitação dos Termos</h2>
        <p>
          Ao acessar e usar o site E-Commerce, você concorda em
          cumprir e estar vinculado a estes Termos de Uso e à nossa Política de
          Privacidade. Se você não concordar com qualquer parte destes termos,
          não deverá utilizar nosso site.
        </p>

        <h2>2. Uso do Site</h2>
        <p>
          Você concorda em usar o site apenas para fins legais e de uma maneira
          que não infrinja os direitos de, restrinja ou iniba o uso e gozo do
          site por qualquer terceiro.
        </p>
        
        <h2>3. Contas de Usuário</h2>
        <p>
          Para acessar certas funcionalidades, você pode ser solicitado a criar
          uma conta. Você é responsável por manter a confidencialidade de sua
          senha e por todas as atividades que ocorram em sua conta.
        </p>

        <h2>4. Propriedade Intelectual</h2>
        <p>
          Todo o conteúdo presente no site, incluindo textos, gráficos, logos e
          imagens, é de nossa propriedade ou de nossos fornecedores e é protegido
          pelas leis de direitos autorais.
        </p>
        
        <h2>5. Limitação de Responsabilidade</h2>
        <p>
          Em nenhuma circunstância o E-Commerce será responsável por
          quaisquer danos indiretos, incidentais, especiais ou consequentes
          resultantes do uso ou da incapacidade de usar nosso site ou produtos.
        </p>
        
        <h2>6. Modificações dos Termos</h2>
        <p>
          Reservamo-nos o direito de modificar estes Termos de Uso a qualquer
          momento. Notificaremos sobre quaisquer alterações postando os novos
          termos no site.
        </p>
    </StaticPageLayout>
  );
};

export default TermosDeUsoPage;