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
]