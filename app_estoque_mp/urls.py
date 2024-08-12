from django.urls import path
from .views import PecaViewSet, LocalizacaoViewSet

urlpatterns = [
    path('materiais/peca/<str:peca>/', PecaViewSet.as_view({'get': 'obter_peca'})),
    path('materiais/localizacoes/<str:localizacao>/', LocalizacaoViewSet.as_view({'get': 'obter_localizacao'})),
]
