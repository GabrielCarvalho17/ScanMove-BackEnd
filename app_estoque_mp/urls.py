from django.urls import path
from .views import EstoqueMateriaisView

urlpatterns = [
    path('materiais/peca/<str:peca>/', EstoqueMateriaisView.as_view({'get': 'retrieve_peca'})),
    path('materiais/localizacoes/<str:localizacao>/', EstoqueMateriaisView.as_view({'get': 'retrieve_localizacao'})),
]
