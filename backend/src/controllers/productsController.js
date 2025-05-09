// src/controllers/productsController.js
import Product from "../models/Product.js";
import Category from "../models/Category.js";
import { validationResult } from "express-validator";
import { uploadImage, deleteImage } from "../utils/cloudinary.js";
import mongoose from "mongoose";
import AppError from "../utils/appError.js";

/**
 * @description Cria um novo produto. Requer upload de imagem via multipart/form-data.
 * @route POST /api/products
 * @access Admin
 */
export const createProduct = async (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  if (!req.file) {
    return next(new AppError("Imagem do produto é obrigatória.", 400));
  }

  let imageUrl = null;
  let imagePublicId = null;

  try {
    // 1. Faz upload da imagem para Cloudinary
    try {
      const result = await uploadImage(req.file.path);
      imageUrl = result.secure_url;
      imagePublicId = result.public_id;
    } catch (uploadError) {
      return next(new AppError("Falha ao fazer upload da imagem.", 500));
    }

    // 2. Monta os dados do produto
    const productData = {
      name: req.body.name,
      price: Number(req.body.price),
      category: req.body.category,
      description: req.body.description,
      stock: req.body.stock ? Number(req.body.stock) : 0,
      image: imageUrl,
      imagePublicId: imagePublicId,
    };

    // 3. Cria o produto no banco de dados
    const product = await Product.create(productData);

    // 4. Popula a categoria para a resposta
    const populatedProduct = await Product.findById(product._id)
      .populate("category", "name slug")
      .lean();

    // 5. Retorna o produto criado
    res.status(201).json(populatedProduct);
  } catch (err) {
    // 6. Tratamento de erro do DB ou outro erro inesperado
    if (err.code === 11000 && err.keyPattern && err.keyPattern.name) {
      return next(
        new AppError(`Produto com nome '${req.body.name}' já existe.`, 409)
      );
    }
    if (imagePublicId) {
      try {
        await deleteImage(imagePublicId);
      } catch (delErr) {
        logger.error("Erro ao deletar imagem órfã:", delErr);
      }
    }
    next(err);
  }
};

/**
 * @description Lista produtos com filtros, paginação e ordenação.
 * @route GET /api/products
 * @access Público
 */
export const getProducts = async (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    const {
      page = 1,
      limit = 10,
      q,
      category: categoryIdentifier,
      sort,
    } = req.query;

    const currentPageNum = parseInt(page, 10);
    const limitNum = parseInt(limit, 10);
    const skip = (currentPageNum - 1) * limitNum;

    const filterQuery = {};

    if (categoryIdentifier) {
      const categoryFilter = mongoose.Types.ObjectId.isValid(
        String(categoryIdentifier)
      )
        ? { _id: categoryIdentifier }
        : { slug: String(categoryIdentifier).toLowerCase() };

      const foundCategory = await Category.findOne(categoryFilter)
        .select("_id")
        .lean();

      if (foundCategory) {
        filterQuery.category = foundCategory._id;
      } else {
        return res.status(200).json({
          status: "success",
          results: 0,
          products: [],
          message: "Categoria não encontrada",
          totalPages: 0,
          currentPage: currentPageNum,
          totalProducts: 0,
        });
      }
    }

    if (q) {
      filterQuery.$text = { $search: String(q) };
    }

    const sortOptions = sort ? String(sort).split(",").join(" ") : "-createdAt";

    const [products, totalProducts] = await Promise.all([
      Product.find(filterQuery)
        .populate("category", "name slug")
        .sort(sortOptions)
        .limit(limitNum)
        .skip(skip)
        .lean(),
      Product.countDocuments(filterQuery),
    ]);

    const totalPages = Math.ceil(totalProducts / limitNum);

    res.status(200).json({
      status: "success",
      results: products.length,
      totalProducts: totalProducts,
      totalPages: totalPages,
      currentPage: currentPageNum,
      products,
    });
  } catch (err) {
    next(err);
  }
};

/**
 * @description Obtém um produto específico pelo seu ID.
 * @route GET /api/products/:id
 * @access Público
 */
export const getProductById = async (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    const productId = req.params.id;
    const product = await Product.findById(productId)
      .populate("category", "name slug")
      .lean();

    if (!product) {
      return next(new AppError("Produto não encontrado.", 404));
    }
    res.status(200).json(product);
  } catch (err) {
    next(err);
  }
};

/**
 * @description Atualiza um produto existente. Permite upload de nova imagem.
 * @route PUT /api/products/:id
 * @access Admin
 */
export const updateProduct = async (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  const productId = req.params.id;
  const updates = { ...req.body };
  let oldPublicId = null;
  let newImageUploaded = false;

  try {
    // 1. Busca o produto existente para pegar o ID da imagem antiga
    const existingProduct = await Product.findById(productId);
    if (!existingProduct) {
      return next(new AppError("Produto não encontrado para atualizar.", 404));
    }
    oldPublicId = existingProduct.imagePublicId;

    // 2. Se uma nova imagem foi enviada
    if (req.file) {
      newImageUploaded = true;
      // 2a. Faz upload da nova imagem PRIMEIRO
      let uploadResult;
      try {
        uploadResult = await uploadImage(req.file.path);
        updates.image = uploadResult.secure_url;
        updates.imagePublicId = uploadResult.public_id;
      } catch (uploadError) {
        return next(new AppError("Falha ao fazer upload da nova imagem.", 500));
      }

      // 2b. Se upload deu certo E existia imagem antiga, deleta a antiga
      if (oldPublicId) {
        try {
          await deleteImage(oldPublicId);
        } catch (cloudinaryErr) {
          logger.error(
            `Falha ao deletar imagem antiga (${oldPublicId}) do Cloudinary após novo upload:`,
            cloudinaryErr
          );
        }
      }
    } else {
      delete updates.image;
      delete updates.imagePublicId;
    }

    // 3. Converte price e stock para Number, se foram enviados
    if (updates.price !== undefined) {
      updates.price = Number(updates.price);
    }
    if (updates.stock !== undefined) {
      updates.stock = Number(updates.stock);
    }
    delete updates.rating;
    delete updates.numReviews;

    // 4. Atualiza o produto no banco de dados
    const product = await Product.findByIdAndUpdate(productId, updates, {
      new: true,
      runValidators: true,
    }).populate("category", "name slug");

    // 5. Verifica se a atualização foi bem-sucedida
    if (!product) {
      if (newImageUploaded && updates.imagePublicId) {
        try {
          await deleteImage(updates.imagePublicId);
        } catch (delErr) {}
      }
      return next(
        new AppError("Produto não encontrado após tentativa de update.", 404)
      );
    }

    // 6. Retorna o produto atualizado
    res.status(200).json(product);
  } catch (err) {
    if (newImageUploaded && updates.imagePublicId) {
      try {
        await deleteImage(updates.imagePublicId);
      } catch (delErr) {
        logger.error("Erro ao deletar img órfã no catch:", delErr);
      }
    }
    if (err.code === 11000 && err.keyPattern && err.keyPattern.name) {
      return next(
        new AppError(`Produto com nome '${updates.name}' já existe.`, 409)
      );
    }
    next(err);
  }
};

/**
 * @description Deleta um produto pelo ID e sua imagem associada no Cloudinary.
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

    // 1. Deleta o produto do banco PRIMEIRO, e pega o documento deletado
    const deletedProduct = await Product.findByIdAndDelete(productId);

    if (!deletedProduct) {
      return next(new AppError("Produto não encontrado para deletar.", 404));
    }

    // 2. Se o produto foi deletado E tinha um imagePublicId, tenta deletar do Cloudinary
    if (deletedProduct.imagePublicId) {
      try {
        await deleteImage(deletedProduct.imagePublicId);
      } catch (cloudinaryErr) {
        logger.error(
          `Produto ${productId} deletado do DB, mas falha ao deletar imagem ${deletedProduct.imagePublicId} do Cloudinary:`,
          cloudinaryErr
        );
      }
    }

    // 3. Retorna sucesso
    res.status(200).json({
      status: "success",
      message: "Produto removido com sucesso",
    });
  } catch (err) {
    next(err);
  }
};
