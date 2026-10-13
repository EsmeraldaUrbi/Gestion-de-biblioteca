from biblioteca.repositories.catalogo_repository import DjangoCatalogoRepository


class LibroNoEncontradoError(Exception):
    pass


class CatalogoService:
    def __init__(self, repository=None):
        self.repository = repository if repository is not None else DjangoCatalogoRepository()

    def listar(self, filtros):
        return self.repository.listar(filtros)

    def obtener(self, libro_id):
        libro = self.repository.obtener(libro_id)
        if libro is None:
            raise LibroNoEncontradoError()
        return libro

    def opciones(self):
        return self.repository.opciones()
