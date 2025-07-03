import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Aplica a máscara de CPF (XXX.XXX.XXX-XX).
 * @param cpf - O CPF a ser formatado.
 * @returns O CPF formatado ou o valor original se for inválido.
 */
export function formatCPF(cpf: string): string {
  const cleaned = cpf.replace(/\D/g, '');
  if (cleaned.length !== 11) {
    return cpf;
  }
  return cleaned.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

/**
 * Aplica a máscara de CEP (XXXXX-XXX).
 * @param cep - O CEP a ser formatado.
 * @returns O CEP formatado ou o valor original se for inválido.
 */
export function formatCEP(cep: string): string {
  const cleaned = cep.replace(/\D/g, '');
  if (cleaned.length !== 8) {
    return cep;
  }
  return cleaned.replace(/(\d{5})(\d{3})/, '$1-$2');
}

/**
 * Aplica a máscara de Telefone ( (XX) XXXXX-XXXX ).
 * @param phone - O telefone a ser formatado.
 * @returns O telefone formatado ou o valor original se for inválido.
 */
export function formatPhone(phone: string): string {
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 11) {
    return cleaned.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }
  if (cleaned.length === 10) {
    return cleaned.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }
  return phone;
}
