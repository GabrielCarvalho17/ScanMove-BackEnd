from django.urls import path
from .views import OrdemProducaoViewSet

urlpatterns = [
    path(
        "producao/inspecoes/criar_inspecao/",
        OrdemProducaoViewSet.as_view({"post": "criar_inspecao"}),
        name="criar_inspecao",
    ),
    # URL para obter a ordem de produção
    path(
        "producao/inspecoes/<str:ordem_producao>/",
        OrdemProducaoViewSet.as_view({"get": "obter_ordem"}),
        name="obter_ordem",
    ),
]
