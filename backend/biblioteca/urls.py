from django.urls import path

# 3.1 Autenticación y permisos.
from biblioteca.presentation.auth_views import (
    AccesoBibliotecarioView,
    AccesoLectorView,
    LoginView,
    LogoutView,
    UsuarioActualView,
)

# Operación de prueba del proyecto.
from biblioteca.presentation.test_views import (
    TestStatusView,
)

# 3.2 Gestión de usuarios.
from biblioteca.presentation.usuarios_views import (
    UsuariosListCreateView,
    UsuarioDetailView,
    RolesListView,
)

# 3.3 Gestión de libros.
from biblioteca.presentation.libros_views import (
    LibrosListCreateView,
    LibroDetailView,
)

# 3.3 Gestión de ejemplares.
from biblioteca.presentation.ejemplares_views import (
    EjemplaresListCreateView,
    EjemplarDetailView,
)

# 3.3 Gestión de autores y categorías.
from biblioteca.presentation.autores_views import (
    AutoresListCreateView,
    AutorDetailView,
)
from biblioteca.presentation.categorias_views import (
    CategoriasListCreateView,
    CategoriaDetailView,
)

# 3.4 Catálogo.
from biblioteca.presentation.catalogo_views import (
    CatalogoListView,
    CatalogoDetailView,
    CatalogoFiltrosView,
)

# 3.5 Registro de préstamos.
from biblioteca.presentation.prestamos_views import (
    BusquedaLectoresView,
    PrestamoElegibilidadView,
    PrestamosRegistroView,
)

# 3.5 Consulta personal de préstamos.
from biblioteca.presentation.mis_prestamos_views import (
    MisPrestamosView,
)

# 3.9 Consulta personal de sanciones.
from biblioteca.presentation.mis_sanciones_views import (
    MisSancionesView as MisSancionesPersonalView,
)

# 3.6 Registro de devoluciones.
from biblioteca.presentation.devoluciones_views import (
    DevolucionRegistroView,
    PrestamosActivosDevolucionView,
)

# 3.8 Consulta de sanciones y registro de pagos.
from biblioteca.presentation.sanciones_views import (
    SancionDetailView,
    SancionPagoView,
    SancionesListView,
)


urlpatterns = [
    # -----------------------------------------
    # Operación de estado
    # -----------------------------------------

    path(
        'estado/',
        TestStatusView.as_view(),
        name='test-estado'
    ),

    # -----------------------------------------
    # 3.1 Autenticación
    # -----------------------------------------

    path(
        'auth/login/',
        LoginView.as_view(),
        name='auth-login'
    ),

    path(
        'auth/logout/',
        LogoutView.as_view(),
        name='auth-logout'
    ),

    path(
        'auth/me/',
        UsuarioActualView.as_view(),
        name='auth-me'
    ),

    path(
        'auth/access/bibliotecario/',
        AccesoBibliotecarioView.as_view(),
        name='auth-access-bibliotecario'
    ),

    path(
        'auth/access/lector/',
        AccesoLectorView.as_view(),
        name='auth-access-lector'
    ),

    # -----------------------------------------
    # 3.2 Usuarios y roles
    # -----------------------------------------

    path(
        'usuarios/',
        UsuariosListCreateView.as_view(),
        name='usuarios-list-create'
    ),

    path(
        'usuarios/<int:usuario_id>/',
        UsuarioDetailView.as_view(),
        name='usuarios-detail'
    ),

    path(
        'roles/',
        RolesListView.as_view(),
        name='roles-list'
    ),

    # -----------------------------------------
    # 3.4 Catálogo
    # -----------------------------------------

    path(
        'catalogo/',
        CatalogoListView.as_view(),
        name='catalogo-list'
    ),

    path(
        'catalogo/filtros/',
        CatalogoFiltrosView.as_view(),
        name='catalogo-filtros'
    ),

    path(
        'catalogo/<int:libro_id>/',
        CatalogoDetailView.as_view(),
        name='catalogo-detail'
    ),

    # -----------------------------------------
    # 3.3 Libros y ejemplares
    # -----------------------------------------

    path(
        'libros/',
        LibrosListCreateView.as_view(),
        name='libros-list-create'
    ),

    path(
        'libros/<int:libro_id>/',
        LibroDetailView.as_view(),
        name='libros-detail'
    ),

    path(
        'ejemplares/',
        EjemplaresListCreateView.as_view(),
        name='ejemplares-list-create'
    ),

    path(
        'ejemplares/<int:ejemplar_id>/',
        EjemplarDetailView.as_view(),
        name='ejemplares-detail'
    ),

    # -----------------------------------------
    # 3.3 Autores y categorías
    # -----------------------------------------

    path(
        'autores/',
        AutoresListCreateView.as_view(),
        name='autores-list-create'
    ),

    path(
        'autores/<int:autor_id>/',
        AutorDetailView.as_view(),
        name='autores-detail'
    ),

    path(
        'categorias/',
        CategoriasListCreateView.as_view(),
        name='categorias-list-create'
    ),

    path(
        'categorias/<int:categoria_id>/',
        CategoriaDetailView.as_view(),
        name='categorias-detail'
    ),

    # -----------------------------------------
    # 3.5 Préstamos de ventanilla
    # -----------------------------------------

    path(
        'prestamos/seleccion/usuarios/',
        BusquedaLectoresView.as_view(),
        name='prestamos-buscar-lectores'
    ),

    path(
        'prestamos/elegibilidad/',
        PrestamoElegibilidadView.as_view(),
        name='prestamos-elegibilidad'
    ),

    path(
        'prestamos/',
        PrestamosRegistroView.as_view(),
        name='prestamos-registro'
    ),

    # -----------------------------------------
    # 3.5 y 3.9 Consulta personal
    # -----------------------------------------

    path(
        'prestamos/mios/',
        MisPrestamosView.as_view(),
        name='prestamos-mios'
    ),

    path(
        'sanciones/mias/',
        MisSancionesPersonalView.as_view(),
        name='sanciones-mias'
    ),

    # -----------------------------------------
    # 3.6 Devoluciones y multas
    # -----------------------------------------

    path(
        'prestamos/<int:prestamo_id>/devolucion/',
        DevolucionRegistroView.as_view(),
        name='prestamos-devolucion'
    ),

    path(
        'devoluciones/prestamos-activos/',
        PrestamosActivosDevolucionView.as_view(),
        name='devoluciones-prestamos-activos'
    ),

    # -----------------------------------------
    # 3.8 Sanciones y pagos
    # -----------------------------------------

    path(
        'sanciones/',
        SancionesListView.as_view(),
        name='sanciones-list'
    ),

    path(
        'sanciones/<int:sancion_id>/',
        SancionDetailView.as_view(),
        name='sanciones-detail'
    ),

    path(
        'sanciones/<int:sancion_id>/pago/',
        SancionPagoView.as_view(),
        name='sanciones-pago'
    ),
]
