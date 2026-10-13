from rest_framework import serializers

from biblioteca.models import Autor, Categoria, Libro


class CatalogoFiltrosSerializer(serializers.Serializer):
    titulo = serializers.CharField(required=False, allow_blank=True, max_length=100)
    autor = serializers.IntegerField(required=False, min_value=1)
    categoria = serializers.IntegerField(required=False, min_value=1)
    disponible = serializers.BooleanField(required=False)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class AutorCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['autor_id', 'nombre']


class CategoriaCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['categoria_id', 'nombre_categoria']


class LibroCatalogoSerializer(serializers.ModelSerializer):
    autores = AutorCatalogoSerializer(many=True, read_only=True)
    categorias = CategoriaCatalogoSerializer(many=True, read_only=True)
    stock_total = serializers.IntegerField(read_only=True)
    stock_disponible = serializers.IntegerField(read_only=True)

    class Meta:
        model = Libro
        fields = [
            'libro_id', 'titulo', 'isbn', 'fecha_publicacion',
            'autores', 'categorias', 'stock_total', 'stock_disponible',
        ]
