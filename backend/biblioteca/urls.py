from django.urls import path
from biblioteca.presentation.test_views import TestStatusView

urlpatterns = [
    path('estado/', TestStatusView.as_view(), name='test-estado'),
]