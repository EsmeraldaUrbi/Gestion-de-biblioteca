from django.db import models

class Rol(models.Model):
    rol_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    limite_prestamos_activos = models.IntegerField()

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    usuario_id = models.AutoField(primary_key=True)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='rol_id')
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    email = models.CharField(max_length=50, unique=True)
    contrasena_hash = models.CharField(max_length=256)

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    categoria_id = models.AutoField(primary_key=True)
    nombre_categoria = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre_categoria


class Autor(models.Model):
    autor_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    nacionalidad = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    libro_id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    fecha_publicacion = models.DateField(null=True, blank=True)
    
    # Relaciones many-to-many explícitas según el diagrama ER
    autores = models.ManyToManyField(Autor, through='LibroAutor')
    categorias = models.ManyToManyField(Categoria, through='CategoriaLibro')

    def __str__(self):
        return self.titulo


class LibroAutor(models.Model):
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE, db_column='autor_id')
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, db_column='libro_id')

    class Meta:
        db_table = 'biblioteca_libros_autores'


class CategoriaLibro(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, db_column='categoria_id')
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, db_column='libro_id')

    class Meta:
        db_table = 'biblioteca_categoria_libros'

class Ejemplar(models.Model):
    ejemplar_id = models.AutoField(primary_key=True)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, db_column='libro_id')
    codigo_inventario = models.CharField(max_length=15)
    estado = models.CharField(max_length=15)

    def __str__(self):
        return f"Ejemplar {self.codigo_inventario} ({self.estado})"


class Prestamo(models.Model):
    prestamo_id = models.AutoField(primary_key=True)
    fecha_prestamo = models.DateField()
    fecha_devolucion = models.DateField(null=True, blank=True)
    fecha_limite = models.DateField()
    ejemplar = models.ForeignKey(Ejemplar, on_delete=models.CASCADE, db_column='ejemplar_id')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='usuario_id')

    def __str__(self):
        return f"Préstamo #{self.prestamo_id}"


class Sancion(models.Model):
    sancion_id = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, db_column='prestamo_id')
    tipo = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField(null=True, blank=True)
    fecha_inicio_bloqueo = models.DateField(null=True, blank=True)
    fecha_fin_bloqueo = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Sanción #{self.sancion_id} - {self.tipo}"