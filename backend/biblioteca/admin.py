from django.contrib import admin
from .models import (
    Rol, Usuario, Categoria, Autor, 
    Libro, LibroAutor, CategoriaLibro, 
    Ejemplar, Prestamo, Sancion
)

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Categoria)
admin.site.register(Autor)
admin.site.register(Libro)
admin.site.register(LibroAutor)
admin.site.register(CategoriaLibro)
admin.site.register(Ejemplar)
admin.site.register(Prestamo)
admin.site.register(Sancion)