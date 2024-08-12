from django.urls import path
from .views import PecaViewSet, LocalizacaoViewSet, MovimentacaoViewSet

urlpatterns = [
    path('materiais/peca/<str:peca>/', PecaViewSet.as_view({'get': 'obter_peca'})),
    path('materiais/localizacoes/<str:localizacao>/', LocalizacaoViewSet.as_view({'get': 'obter_localizacao'})),
    path('materiais/movimentacoes/', MovimentacaoViewSet.as_view({'get': 'listar_movimentacoes', 'post': 'criar_movimentacao'})),
    path('materiais/movimentacoes/<int:movimentacao>/', MovimentacaoViewSet.as_view({'get': 'obter_movimentacao'})),
]
