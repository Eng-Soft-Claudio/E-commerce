/**
 * @file Componente de exibição de categorias em destaque.
 * @description Renderiza uma grade de categorias clicáveis com ícones ou
 * placeholders, servindo como um ponto de navegação principal na página inicial.
 */

'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ImageIcon } from 'lucide-react'; // Ícone para placeholder

// --- TIPOS DE DADOS ---

interface Category {
  id: number;
  title: string;
}

interface FeaturedCategoriesProps {
  categories: Category[];
}

/**
 * Mapeia um slug de categoria para a URL de sua imagem correspondente.
 * Usar `Record<string, string>` é mais explícito e seguro do que um objeto genérico.
 */
const imageUrlMap: Record<string, string> = {
  'categoria_1':
    'https://res.cloudinary.com/cloud-drone/image/upload/v1751242471/categoria3_qwpzrm.png',
  'categoria_2':
    'https://res.cloudinary.com/cloud-drone/image/upload/v1751242471/categoria2_umszpi.png',
  'categoria_3':
    'https://res.cloudinary.com/cloud-drone/image/upload/v1751242471/categoria1_b2osso.png',
    'categoria_4':
    'https://res.cloudinary.com/cloud-drone/image/upload/v1751242471/categoria3_qwpzrm.png',
};


const FeaturedCategories = ({ categories }: FeaturedCategoriesProps) => {
  if (!categories || categories.length === 0) return null;

  return (
    <section className="bg-gray-50 w-full" aria-labelledby="featured-categories-title">
      <div className="container mx-auto px-4 py-16">
        <h2
          id="featured-categories-title"
          className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 text-center mb-10"
        >
          CLIQUE E CONHEÇA
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4 md:gap-6">
          {categories.map((category) => {
            const imageKey = category.title.toLowerCase();
            const imageUrl = imageUrlMap[imageKey];

            return (
              <Link
                key={category.id}
                href={`/category/${category.id}`}
                className="group block text-center transition-transform duration-300 ease-in-out hover:-translate-y-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-black rounded-lg"
                aria-label={`Ver produtos da categoria ${category.title}`}
              >
                <div className="relative aspect-square w-full rounded-lg bg-gray-200 flex flex-col items-center justify-center p-2 shadow-sm group-hover:shadow-lg transition-shadow">
                  {/* Container para a imagem ou placeholder */}
                  <div className="relative w-3/4 h-3/4 flex items-center justify-center">
                    {imageUrl ? (
                      <Image
                        src={imageUrl}
                        alt={`Ilustração para a categoria ${category.title}`}
                        fill
                        className="object-contain"
                        sizes="(max-width: 640px) 40vw, (max-width: 1024px) 25vw, 12vw"
                      />
                    ) : (
                      // Melhoria: Mostra um ícone de placeholder se a imagem não for encontrada.
                      <div className="flex flex-col items-center text-gray-500">
                        <ImageIcon size={40} strokeWidth={1.5} />
                        <span className="sr-only">Imagem não disponível</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Nome da Categoria abaixo da imagem */}
                <h3 className="font-semibold uppercase tracking-wider text-xs sm:text-sm mt-2 text-gray-800 group-hover:text-black">
                  {category.title}
                </h3>
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default FeaturedCategories;
