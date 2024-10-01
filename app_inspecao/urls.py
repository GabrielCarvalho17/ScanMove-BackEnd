from django.urls import path
from .views import OrdemProducaoViewSet

urlpatterns = [
    path(
        "producao/inspecoes/",
        OrdemProducaoViewSet.as_view({"post": "criar_inspecao"}),
    ),
    path(
        "producao/inspecoes/<str:ordem_producao>/",
        OrdemProducaoViewSet.as_view(
            {
                "get": "obter_ordem",
                "delete": "excluir_inspecao",
                "patch": "atualizar_status",
            }
        ),
    ),
    # path("producao/inspecoes/<str:ordem_producao>/pecas/", OrdemProducaoViewSet.as_view({"post": "incluir_peca"}),),
    # path("producao/inspecoes/<str:ordem_producao>/pecas/<int:peca_id>/", OrdemProducaoViewSet.as_view({"patch": "atualizar_peca","delete": "excluir_peca",}),),
]
