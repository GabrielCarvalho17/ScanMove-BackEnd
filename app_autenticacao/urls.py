from django.urls import path, include
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from .views import UsuarioView, CustomTokenObtainPairView, CustomTokenRefreshView

router = DefaultRouter()
router.register(r'usuarios', UsuarioView, basename='usuario')

urlpatterns = [
    path('schema/', cache_page(60*15)(SpectacularAPIView.as_view()), name='schema'),  # Cache de 15 minutos
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('', RedirectView.as_view(url='/admin/login/', permanent=True)),
    path('', include(router.urls)),  # Inclui as rotas diretamente
    path('', include('app_estoque_mp.urls')),  # Incluir as rotas do app_estoque_mp sem prefixo adicional
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]
