from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from app_inspecao.services import OrdemProducaoService
from .serializers import OrdemInspecaoSerializer
from rest_framework.decorators import action


class OrdemProducaoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Inspeção"],
        operation_id="obter_ordem",
        parameters=[
            OpenApiParameter(
                name="ordem_producao",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
        responses={
            200: OrdemInspecaoSerializer,
            400: OpenApiResponse(description="A Ordem de produção é obrigatória."),
            404: OpenApiResponse(description="Ordem de produção não encontrada."),
        },
    )
    def obter_ordem(self, request, ordem_producao):
        if not ordem_producao:
            return Response(
                {"mensagem": "A Ordem de produção é obrigatória"}, status=400
            )

        ordem_insp = OrdemProducaoService().obter_ordem_inspecao(ordem_producao)
        if ordem_insp is not None:
            ordem_insp = OrdemInspecaoSerializer(ordem_insp)
            return Response(ordem_insp.data, status=200)

        ordem_prod = OrdemProducaoService().obter_ordem_producao(ordem_producao)
        if ordem_prod is not None:

            ordem_prod = OrdemInspecaoSerializer(ordem_prod)
            return Response(ordem_prod.data, status=200)

        return Response({"mensagem": "Ordem de produção não encontrada"}, status=404)

    @extend_schema(
        tags=["Inspeção"],
        operation_id="criar_inspecao",
        request={
            "application/json": {
                "type": "object",
                "properties": {"ordem_producao": {"type": "string"}},
            }
        },
        responses={
            201: OpenApiResponse(description="Inspeção criada com sucesso."),
            400: OpenApiResponse(description="A Ordem de produção é obrigatória."),
            500: OpenApiResponse(description="Erro ao criar a inspeção."),
        },
    )

    def criar_inspecao(self, request):
        # Printando o corpo da requisição para ver o que está chegando
        print("Dados recebidos no request:", request.data)

        # Extraindo a ordem de produção da requisição
        ordem_producao = request.data.get("ordem_producao")
        print("Ordem de Produção extraída:", ordem_producao)

        # Verificação se a ordem de produção foi fornecida
        if not ordem_producao:
            print("Ordem de Produção não fornecida")
            return Response(
                {"mensagem": "A Ordem de produção é obrigatória."},
                status=400,
            )

        # Chamando o serviço para criar a inspeção
        print("Chamando serviço para criar inspeção...")
        sucesso, mensagem, ordem_data = OrdemProducaoService().criar_inspecao(ordem_producao, request.user.id)

        # Se a inspeção não foi criada (None indica que não encontrou a ordem)
        if sucesso is None:
            return Response({"mensagem": mensagem, "dados:": ordem_data}, status=404)

        # Se a inspeção foi criada com sucesso
        elif sucesso:
            return Response({"mensagem": mensagem, "dados:": ordem_data}, status=201)

        # Caso tenha ocorrido um erro ao criar a inspeção
        else:
            return Response({"mensagem": mensagem, "dados:": ordem_data}, status=500)
