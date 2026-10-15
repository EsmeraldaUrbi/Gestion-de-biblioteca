export interface AutorCatalogo {
  autor_id: number;
  nombre: string;
}

export interface CategoriaCatalogo {
  categoria_id: number;
  nombre_categoria: string;
}

export interface LibroCatalogo {
  libro_id: number;
  titulo: string;
  isbn: string;
  fecha_publicacion: string | null;
  autores: AutorCatalogo[];
  categorias: CategoriaCatalogo[];
  stock_total: number;
  stock_disponible: number;
}

export interface CatalogoFiltros {
  titulo?: string;
  autor?: number;
  categoria?: number;
  disponible?: boolean;
  page?: number;
  page_size?: number;
}

export interface CatalogoOpciones {
  autores: AutorCatalogo[];
  categorias: CategoriaCatalogo[];
}

export interface CatalogoResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: LibroCatalogo[];
}
