// src/controllers/products.js
import Product from '../models/Product.js';
import Category from '../models/Category.js';
import { validationResult } from 'express-validator';
import { uploadImage, deleteImage } from '../utils/cloudinary.js';
import { triggerWebhook } from './webhooks.js';
import mongoose from 'mongoose'; 
import AppError from '../utils/appError.js'; 

/**
 * @description Cria um novo produto. Espera que Multer (upload.single) e as validações rodem ANTES na rota.
 * @route POST /api/products
 * @access Admin
 */

export const createProduct = async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    try {

        if (!req.file) {
            console.error("Controller createProduct: req.file não definido após middlewares.");
            return res.status(400).json({ error: 'Arquivo de imagem obrigatório não encontrado.' });
        }
        console.log("EXECUTANDO createProduct - Antes do uploadImage");
        const result = await uploadImage(req.file.path);
        console.log("EXECUTANDO createProduct - Após uploadImage, result:", result);
        const productData = {
            name: req.body.name,
            price: Number(req.body.price), 
            category: req.body.category, 
            description: req.body.description, 
            stock: req.body.stock ? Number(req.body.stock) : 0,
            image: result.secure_url,   
            imagePublicId: result.public_id 
        };

        const product = await Product.create(productData);
        
        await triggerWebhook('product_created', product);

        const populatedProduct = await Product.findById(product._id)
            .populate('category', 'name slug') 
            .lean();

        res.status(201).json(populatedProduct); 

    } catch (err) {
        console.error("ERRO NO CATCH de createProduct:", err);
        next(err); 
    }
};

/**
 * @description Lista produtos com filtros, paginação e ordenação.
 * @route GET /api/products
 * @access Public (ou conforme definido na rota)
 */

export const getProducts = async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    try {
        const { page = 1, limit = 10, q, category: categoryIdentifier, sort } = req.query;
        const filterQuery = {}; 

        if (categoryIdentifier) {
            let foundCategory = await Category.findOne({
                $or: [
                    { _id: mongoose.Types.ObjectId.isValid(categoryIdentifier) ? categoryIdentifier : null },
                    { slug: categoryIdentifier.toLowerCase() }
                ]
            }).select('_id').lean(); 

            if (foundCategory) {
                filterQuery.category = foundCategory._id;
            } else {
                return res.status(200).json({
                    status: 'success',
                    results: 0,
                    products: [],
                    message: "Categoria não encontrada",
                    totalPages: 0,
                    currentPage: page,
                    totalProducts: 0
                });;
            }
        }

        if (q) {
            filterQuery.$text = { $search: q };
        }

        const sortOptions = sort ? String(sort).split(',').join(' ') : '-createdAt';

        const [products, totalProducts] = await Promise.all([
            Product.find(filterQuery)              
                   .populate('category', 'name slug')
                   .sort(sortOptions)
                   .limit(limit)
                   .skip((page - 1) * limit)
                   .lean(),
            Product.countDocuments(filterQuery)     
        ]);

        const totalPages = Math.ceil(totalProducts / limit);

        res.status(200).json({
            status: 'success',
            results: products.length, 
            totalProducts: totalProducts, 
            totalPages: totalPages,       
            currentPage: page,          
            products,                  
        });

    } catch (err) {
        next(err);
    }
};

/**
 * @description Atualiza um produto existente. Espera que Multer e validações rodem ANTES na rota.
 * @route PUT /api/products/:id
 * @access Admin
 */

export const updateProduct = async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    try {
        const updates = { ...req.body }; 
        const productId = req.params.id;
        let oldPublicId = null; 

        const existingProduct = await Product.findById(productId).lean();
        if (!existingProduct) {
             return next(new AppError('Produto não encontrado para atualizar.', 404));
        }
        oldPublicId = existingProduct.imagePublicId; 

        if (req.file) {
            if (oldPublicId) {
                try {
                    await deleteImage(oldPublicId);
                } catch (cloudinaryErr) {
                    console.error(`Falha ao deletar imagem antiga ${oldPublicId} do Cloudinary durante update:`, cloudinaryErr.message);
                }
            }
            console.log("EXECUTANDO updateProduct - Antes do uploadImage"); 
            const result = await uploadImage(req.file.path);
            console.log("EXECUTANDO updateProduct - Após uploadImage, result:", result);
            updates.image = result.secure_url;       
            updates.imagePublicId = result.public_id; 
        } else {
             delete updates.imagePublicId;
        }
        if (updates.price !== undefined) {
            updates.price = Number(updates.price);
        }
        if (updates.stock !== undefined) {
            updates.stock = Number(updates.stock);
        }
        
        const product = await Product.findByIdAndUpdate(
            productId,
            updates, 
            { new: true, runValidators: true }
        ).populate('category', 'name slug');

        if (!product) {
            return next(new AppError('Produto não encontrado após tentativa de update.', 404)); // Pouco provável
        }
        await triggerWebhook('product_updated', product);

        res.status(200).json(product);

    } catch (err) {
        console.error("ERRO NO CATCH de updateProduct:", err);
        next(err);
    }
};

/**
 * @description Deleta um produto pelo ID.
 * @route DELETE /api/products/:id
 * @access Admin
 */

export const deleteProduct = async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    try {
        const productId = req.params.id;

        const product = await Product.findById(productId).lean(); 

        if (!product) {
            return next(new AppError('Produto não encontrado para deletar.', 404));
        }

        if (product.imagePublicId) {
            try {
                await deleteImage(product.imagePublicId);
            } catch (cloudinaryErr) {
                console.error(`Falha ao deletar imagem ${product.imagePublicId} do Cloudinary durante deleção do produto ${productId}:`, cloudinaryErr.message);
            }
        } else {
             console.warn(`Produto ${productId} não possuía imagePublicId para deletar do Cloudinary.`);
        }

        const deletedProduct = await Product.findByIdAndDelete(productId);

        if (!deletedProduct) {
            return next(new AppError('Produto não encontrado ao tentar deletar do DB (após busca inicial).', 404));
        }

        res.status(200).json({ 
            status: 'success',
            message: 'Produto removido com sucesso',
        });

    } catch (err) {
        
        next(err);
    }
};