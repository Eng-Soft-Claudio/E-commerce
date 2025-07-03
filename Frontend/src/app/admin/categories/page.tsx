/**
 * @file Página administrativa para gerenciamento de categorias.
 * @description Permite que superusuários visualizem, criem, editem e deletem categorias de produtos.
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Cookies from 'js-cookie';
import { PlusCircle, Edit, Trash2, Loader2 } from 'lucide-react';

import AdminLayout from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { CategoryForm, CategoryFormValues } from '@/components/admin/CategoryForm';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Interface que define a estrutura de dados de uma Categoria.
 */
interface Category {
  id: number;
  title: string;
  description?: string | null;
}

/**
 * Componente principal da página de gerenciamento de categorias.
 */
const AdminCategoriesPage = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Busca a lista de categorias da API de forma assíncrona.
   * Utiliza useCallback para memoizar a função e evitar recriações desnecessárias.
   */
  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/categories/`);
      if (!response.ok) {
        throw new Error(`Falha ao buscar categorias: ${response.statusText}`);
      }
      const data: Category[] = await response.json();
      setCategories(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Um erro inesperado ocorreu.';
      console.error('Erro em fetchCategories:', err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  /**
   * Lida com o envio do formulário para criar ou editar uma categoria.
   * @param {CategoryFormValues} values
   */
  const handleFormSubmit = async (values: CategoryFormValues) => {
    setIsSubmitting(true);
    const token = Cookies.get('access_token');
    const method = editingCategory ? 'PUT' : 'POST';
    const url = editingCategory
      ? `${API_URL}/categories/${editingCategory.id}`
      : `${API_URL}/categories/`;

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Falha ao salvar a categoria.');
      }

      setIsDialogOpen(false);
      setEditingCategory(null);
      await fetchCategories();
    } catch (err) {
      console.error('Erro em handleFormSubmit:', err);
      const errorMessage = err instanceof Error ? err.message : 'Um erro inesperado ocorreu.';
      alert(`Erro: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Lida com a exclusão de uma categoria.
   * @param {number} categoryId
   */
  const handleDelete = async (categoryId: number) => {
    if (
      !window.confirm(
        'Tem certeza que deseja deletar esta categoria? Todos os produtos associados também podem ser afetados.',
      )
    )
      return;

    const token = Cookies.get('access_token');
    try {
      const response = await fetch(`${API_URL}/categories/${categoryId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Falha ao deletar a categoria.');
      }
      await fetchCategories();
    } catch (err) {
      console.error('Erro em handleDelete:', err);
      const errorMessage = err instanceof Error ? err.message : 'Um erro inesperado ocorreu.';
      alert(`Erro: ${errorMessage}`);
    }
  };

  return (
    <AdminLayout>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-800">Gerenciar Categorias</h1>
        <Dialog
          open={isDialogOpen}
          onOpenChange={(isOpen) => {
            if (!isOpen) {
              setEditingCategory(null);
            }
            setIsDialogOpen(isOpen);
          }}
        >
          <DialogTrigger asChild>
            {/* O botão fica desabilitado se houver um erro inicial ao carregar a página */}
            <Button onClick={() => setEditingCategory(null)} disabled={loading || !!error}>
              <PlusCircle className="mr-2 h-4 w-4" />
              Adicionar Categoria
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingCategory ? 'Editar Categoria' : 'Adicionar Nova Categoria'}
              </DialogTitle>
            </DialogHeader>
            <CategoryForm
              onSubmit={handleFormSubmit}
              initialData={editingCategory || undefined}
              isLoading={isSubmitting}
            />
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md overflow-x-auto">
        {loading ? (
          <div className="flex justify-center items-center py-10">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
            <p className="ml-3 text-gray-600">Carregando categorias...</p>
          </div>
        ) : error ? ( // Exibe o erro na UI
          <div className="text-center py-10 text-red-600">
            <p>
              <strong>Erro ao carregar dados:</strong> {error}
            </p>
          </div>
        ) : (
          <Table className="min-w-full table-fixed">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[10%]">ID</TableHead>
                <TableHead className="w-[30%]">Título</TableHead>
                <TableHead className="w-[40%]">Descrição</TableHead>
                <TableHead className="w-[20%] text-center">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {categories.map((category) => (
                <TableRow key={category.id}>
                  <TableCell className="font-medium">{category.id}</TableCell>
                  <TableCell className="truncate">{category.title}</TableCell>
                  <TableCell className="truncate">{category.description || 'N/A'}</TableCell>
                  <TableCell className="text-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setEditingCategory(category);
                        setIsDialogOpen(true);
                      }}
                      aria-label={`Editar categoria ${category.title}`}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(category.id)}
                      aria-label={`Deletar categoria ${category.title}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </AdminLayout>
  );
};

export default AdminCategoriesPage;
