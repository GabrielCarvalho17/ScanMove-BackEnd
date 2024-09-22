from django.urls import path
from .views import OrdemProducaoViewSet

urlpatterns = [
    # URL para obter a ordem de produção
    path(
        "producao/ordem_producao/<str:ordem_producao>/", 
        OrdemProducaoViewSet.as_view({"get": "obter_ordem"}), 
        name="obter_ordem"
    ),
    
]
