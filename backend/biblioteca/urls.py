from biblioteca.presentation.catalogo_views import (
    CatalogoListView, CatalogoDetailView, CatalogoFiltrosView,
)

from django.urls import path

from biblioteca.presentation.auth_views import (
    AccesoBibliotecarioView,
    AccesoLectorView,
    LoginView,
    LogoutView,
    UsuarioActualView,
)
from biblioteca.presentation.test_views import (
    TestStatusView,
)

#Importaiones para ticket 3.2
from biblioteca.presentation.usuarios_views import (
    UsuariosListCreateView,
    UsuarioDetailView,
    RolesListView,
)

# Importaciones para ticket 3.3
from biblioteca.presentation.libros_views import (
    LibrosListCreateView,
    LibroDetailView,
)

urlpatterns = [
    path(
        'estado/',
        TestStatusView.as_view(),
        name='test-estado'
    ),

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

    #3.2
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
    path('catalogo/', CatalogoListView.as_view(), name='catalogo-list'),
    path('catalogo/filtros/', CatalogoFiltrosView.as_view(), name='catalogo-filtros'),
    path('catalogo/<int:libro_id>/', CatalogoDetailView.as_view(), name='catalogo-detail'),

    # 3.3 Libros
    path('libros/', LibrosListCreateView.as_view(), name='libros-list-create'),
    path('libros/<int:libro_id>/', LibroDetailView.as_view(), name='libros-detail'),
]
