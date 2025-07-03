/**
 * @file Página "Quem Somos".
 * @description Apresenta a história, missão, visão e valores da empresa.
 */

import React from 'react';
import type { Metadata } from 'next';

import StaticPageLayout from '@/components/layout/StaticPageLayout';

/**
 * Metadados da página para SEO.
 */
export const metadata: Metadata = {
  title: 'Quem Somos | E-Commerce',
  description: 'Conheça a nossa história, nossa missão e o que nos inspira a servir você.',
};

/**
 * Componente da página "Quem Somos".
 */
const QuemSomosPage = () => {
  return (
    <StaticPageLayout title="Nossa História">
      <p>
        Bem-vindo à E-Commerce. Nascemos de um profundo desejo de espalhar a felicidade através de artigos exclusivos de alta qualidade, que sirvam como inspiração no dia a dia de nossos clientes.
      </p>

      <h2>Nossa Missão</h2>
      <p>
        Nossa missão é ser uma ponte entre a felicidade e as pessoas, oferecendo produtos de qualidade superior.
      </p>

      <h2>Visão e Valores</h2>
      <ul>
        <li>
          <strong>Garra:</strong> O pilar que sustenta todas as nossas ações.
        </li>
        <li>
          <strong>Qualidade:</strong> Comprometimento com a excelência em cada produto que
          oferecemos.
        </li>
        <li>
          <strong>Respeito:</strong> Tratamos cada cliente com a dignidade e a atenção que merecem.
        </li>
        <li>
          <strong>Comunidade:</strong> Buscamos construir uma comunidade unida.
        </li>
      </ul>

      <p>Agradecemos por nos permitir fazer parte do seu dia-a-dia.</p>
    </StaticPageLayout>
  );
};

export default QuemSomosPage;
