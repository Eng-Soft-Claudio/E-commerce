/**
 * @file Componente do Rodapé (Footer) da aplicação.
 * @description Renderiza o rodapé global, contendo links institucionais,
 * informações de contato, métodos de pagamento e copyright.
 */

import React from 'react';
import Link from 'next/link';
import {
  CreditCard,
  Banknote,
  QrCode,
} from 'lucide-react';


const footerSections = [
  {
    title: 'Institucional',
    links: [
      { text: 'Quem Somos', href: '/sobre-nos' },
      { text: 'Política de Privacidade', href: '/politica-de-privacidade' },
      { text: 'Termos de Uso', href: '/termos-de-uso' },
    ],
  },
  {
    title: 'Endereço',
    lines: ['Rua Exemplo, 123 - Centro', 'Cidade-UF', 'CEP: 00000-000'],
  },
  {
    title: 'Telefones',
    lines: ['(11) 99999-8888', '(21) 88888-7777'],
  },
  {
    title: 'E-mails',
    links: [
      { text: 'info@email.com', href: 'mailto:info@email.com' },
      { text: 'pedido@email.com', href: 'mailto:pedido@email.com' },
    ],
  },
];

const paymentMethods = [
  { name: 'Pix', icon: QrCode },
  { name: 'Cartão de Crédito ou Débito', icon: CreditCard },
  { name: 'Boleto', icon: Banknote },
];


/**
 * Subcomponente para renderizar uma coluna de links do rodapé.
 */
const FooterColumn = ({
  title,
  links,
  lines,
}: {
  title: string;
  links?: { text: string; href: string }[];
  lines?: string[];
}) => (
  <div>
    <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">{title}</h3>
    <ul className="space-y-2">
      {lines?.map((line, index) => (
        <li key={index} className="text-sm">
          {line}
        </li>
      ))}
      {links?.map((link) => (
        <li key={link.text}>
          <Link
            href={link.href}
            className="text-sm text-gray-400 hover:text-white hover:underline transition-colors"
          >
            {link.text}
          </Link>
        </li>
      ))}
    </ul>
  </div>
);


const Footer = () => {
  return (
    <footer className="bg-black text-gray-400">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          {footerSections.map((section) => (
            <FooterColumn key={section.title} {...section} />
          ))}
        </div>

        {/* Seção de Pagamentos */}
        <div className="border-t border-gray-800 pt-8">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider text-center mb-4">
            Formas de Pagamento
          </h3>
          <div className="flex justify-center items-center flex-wrap gap-x-6 gap-y-2">
            {paymentMethods.map((method) => (
              <div
                key={method.name}
                className="flex items-center gap-2 text-gray-300"
                title={method.name}
              >
                {method.icon && <method.icon className="h-5 w-10" />}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Barra de Copyright */}
      <div className="bg-gray-900 py-4">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-gray-500">
          <p>© {new Date().getFullYear()} - E-commerce | CNPJ: XX.YYY.XXX/YYYY-XX</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
