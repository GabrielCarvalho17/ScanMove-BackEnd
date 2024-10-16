from django.urls import path, include
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from .views import UsuarioView, ObterTokensView, RenovarTokensView

router = DefaultRouter()
router.register(r'usuarios', UsuarioView, basename='usuario')

urlpatterns = [
    path('schema/', cache_page(60*15)(SpectacularAPIView.as_view()), name='schema'),  # Cache de 15 minutos
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('', RedirectView.as_view(url='/admin/login/', permanent=True)),
    path('', include(router.urls)),  # Inclui as rotas diretamente
    path('token/', ObterTokensView.as_view(), name='obter_token'),
    path('token/refresh/', RenovarTokensView.as_view(), name='renovar_token'),
]
