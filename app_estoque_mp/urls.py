from django.urls import path
from .views import PecaViewSet, LocalizacaoViewSet, MovimentacaoViewSet

urlpatterns = [
    path("materiais/peca/<str:peca>/", PecaViewSet.as_view({"get": "obter_peca"})),
    path(
        "materiais/localizacao/<str:localizacao>/",
        LocalizacaoViewSet.as_view({"get": "obter_localizacao"}),
    ),
    path(
        "materiais/movimentacoes/",
        MovimentacaoViewSet.as_view(
            {"get": "listar_movimentacoes", "post": "criar_movimentacao"}
        ),
    ),
    path(
        "materiais/movimentacoes/<int:movimentacao>/",
        MovimentacaoViewSet.as_view(
            {
                "get": "obter_movimentacao",
                "delete": "excluir_movimentacao",
                "patch": "atualizar_movimentacao",
            }
        ),
    ),
    path(
        "materiais/movimentacoes/<int:movimentacao>/data_modificacao/<str:data_modificacao>/excluir_pecas/<str:pecas_ids>/",
        MovimentacaoViewSet.as_view({"delete": "excluir_pecas"}),
    ),
    path(
        "materiais/movimentacoes/<int:movimentacao>/incluir_pecas/",
        MovimentacaoViewSet.as_view({"post": "incluir_pecas"}),
    ),
]
