// .eslintrc.js
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'react', 'react-hooks', 'jsx-a11y', 'prettier'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'next/core-web-vitals', // Configuração essencial do Next.js
    'prettier', // Desativa regras do ESLint que conflitam com o Prettier
    'plugin:prettier/recommended', // Integra Prettier como uma regra do ESLint
  ],
  rules: {
    'prettier/prettier': 'warn', // Mostra erros do Prettier como warnings
    'react/react-in-jsx-scope': 'off', // O Next.js já importa o React
    'react/prop-types': 'off', // Já usamos TypeScript para isso
    '@typescript-eslint/no-unused-vars': ['warn', { 'argsIgnorePattern': '^_' }], // Avisa sobre variáveis não usadas
    '@typescript-eslint/no-explicit-any': 'warn', // Avisa sobre o uso de 'any'
    'jsx-a11y/anchor-is-valid': [ // Next.js <Link> já cuida disso
      'error',
      {
        components: ['Link'],
        specialLink: ['hrefLeft', 'hrefRight'],
        aspects: ['invalidHref', 'preferButton'],
      },
    ],
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};