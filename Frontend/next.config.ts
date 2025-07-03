/**
 * @file Arquivo de configuração principal do Next.js.
 * @description Este arquivo permite customizar o comportamento do Next.js, como
 * a configuração de otimização de imagens, redirecionamentos, headers, e mais.
 */

import type { NextConfig } from 'next';

/**
 * @type {NextConfig}
 */
const nextConfig: NextConfig = {
  /**
   * Configuração do componente <Image> e da API de Otimização de Imagens do Next.js.
   * Permite especificar quais domínios externos são autorizados a servir imagens.
   */
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        /**
         * Hostname do Cloudinary.
         * Adicionar este padrão permite que o Next.js otimize imagens
         * servidas a partir do nosso provedor de armazenamento de mídia.
         */
        hostname: 'res.cloudinary.com',
        port: '',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;