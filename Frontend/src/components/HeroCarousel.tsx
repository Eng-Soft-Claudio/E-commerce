/**
 * @file Componente do Carrossel de Banners da Página Inicial.
 * @description Renderiza um carrossel de imagens responsivo com navegação e
 * reprodução automática, utilizando o shadcn/ui Carousel e o plugin Embla Autoplay.
 */

'use client';

import React from 'react';
import Image from 'next/image';

import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel';

import Autoplay from 'embla-carousel-autoplay';

/**
 * Array de objetos que define os banners a serem exibidos no carrossel.
 * Manter os dados aqui centralizados facilita a atualização dos banners no futuro.
 */
const BANNER_DATA = [
  {
    id: 1,
    src: 'https://res.cloudinary.com/cloud-drone/image/upload/v1751242011/banner1_sxlchy.png',
    alt: 'Banner promocional.',
  },
  {
    id: 2,
    src: 'https://res.cloudinary.com/cloud-drone/image/upload/v1751242011/banner2_i1frnk.png',
    alt: 'Banner promocional.',
  },
  {
    id: 3,
    src: 'https://res.cloudinary.com/cloud-drone/image/upload/v1751242011/banner3_ysp2kw.png',
    alt: 'Banner promocional.',
  },
  {
    id: 4,
    src: 'https://res.cloudinary.com/cloud-drone/image/upload/v1751242011/banner4_k0njzh.png',
    alt: 'Banner promocional.',
  },
];


const HeroCarousel = () => {
  return (
    <section className="w-full" aria-label="Carrossel de banners promocionais">
      <Carousel
        plugins={[
          Autoplay({
            delay: 5000, 
            stopOnInteraction: false, 
            stopOnMouseEnter: true, 
          }),
        ]}
        opts={{
          align: 'start', 
          loop: true, 
        }}
        className="w-full"
      >
        <CarouselContent>
          {BANNER_DATA.map((banner) => (
            <CarouselItem key={banner.id}>
              <div className="relative w-full h-[250px] md:h-[400px] lg:h-[500px] xl:h-[550px]">
                <Image
                  src={banner.src}
                  alt={banner.alt} 
                  fill
                  style={{ objectFit: 'cover' }}
                  priority={banner.id === 1}
                  sizes="100vw"
                />
              </div>
            </CarouselItem>
          ))}
        </CarouselContent>
        {/*
          Os controles de navegação são estilizados para melhor visibilidade e usabilidade,
          ficando posicionados sobre a imagem com um fundo semi-transparente.
        */}
        <CarouselPrevious className="absolute left-2 md:left-4 top-1/2 -translate-y-1/2 bg-black/40 text-white border-none hover:bg-black/60 transition-colors" />
        <CarouselNext className="absolute right-2 md:right-4 top-1/2 -translate-y-1/2 bg-black/40 text-white border-none hover:bg-black/60 transition-colors" />
      </Carousel>
    </section>
  );
};

export default HeroCarousel;
