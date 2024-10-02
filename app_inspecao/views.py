from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from app_inspecao.services import OrdemProducaoService
from .serializers import AtualizarStatusSerializer, OrdemInspecaoSerializer
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
            201: OrdemInspecaoSerializer,
            400: OpenApiResponse(description="A Ordem de produção é obrigatória."),
            404: OpenApiResponse(description="Ordem de produção não encontrada."),
            409: OpenApiResponse(description="Erro ao criar a inspeção."),
        },
    )
    def criar_inspecao(self, request):

        ordem_producao = request.data.get("ordem_producao")

        if not ordem_producao:
            print("Ordem de Produção não fornecida")
            return Response(
                {"mensagem": "A Ordem de produção é obrigatória."},
                status=400,
            )

        sucesso, mensagem, ordem_data = OrdemProducaoService().criar_inspecao(
            ordem_producao, request.user.id
        )

        if sucesso is None:
            return Response({"mensagem": mensagem}, status=404)

        if sucesso:
            ordem_data = OrdemInspecaoSerializer(ordem_data)
            return Response(ordem_data.data, status=201)

        return Response({"mensagem": mensagem}, status=409)

    @extend_schema(
        tags=["Inspeção"],
        operation_id="excluir_inspecao",
        responses={
            200: OrdemInspecaoSerializer,
            400: OpenApiResponse(description="A Ordem de produção é obrigatória."),
            404: OpenApiResponse(
                description="Inspeção não encontrada para a ordem de produção fornecida."
            ),
            409: OpenApiResponse(description="Erro ao excluir a inspeção."),
        },
    )
    def excluir_inspecao(self, request, ordem_producao=None):

        if not ordem_producao:
            return Response(
                {
                    "mensagem": "A Ordem de produção é obrigatória para realizar a exclusão."
                },
                status=400,
            )

        status, mensagem, ordem_data = OrdemProducaoService().excluir_inspecao(
            ordem_producao
        )

        if status == 404:
            return Response({"mensagem": mensagem}, status=404)

        if status == 200:
            ordem_data = OrdemInspecaoSerializer(ordem_data)
            return Response(ordem_data.data, status=200)

        return Response({"mensagem": mensagem}, status=409)

    @extend_schema(
        tags=["Inspeção"],
        operation_id="atualizar_status",
        request={
            "application/json": {
                "type": "object",
                "properties": {"status": {"type": "string"}},
            }
        },
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "data_alteracao": {
                            "type": "string",
                            "format": "date-time",
                        }
                    },
                }
            ),
            400: OpenApiResponse(
                description="Ordem de produção e status são obrigatórios."
            ),
            404: OpenApiResponse(
                description="Inspeção não encontrada para a ordem de produção fornecida."
            ),
            409: OpenApiResponse(description="Erro ao atualizar o status."),
        },
    )
    def atualizar_status(self, request, ordem_producao=None):
        if not ordem_producao:
            return Response(
                {
                    "mensagem": "A Ordem de produção é obrigatória para atualizar o status."
                },
                status=400,
            )

        # Captura o novo status e o ID do usuário da requisição
        novo_status = request.data.get("status")
        usuario_id = request.user.id

        # Verifica se o campo "status" foi fornecido
        if not novo_status:
            return Response(
                {"mensagem": "O campo 'status' é obrigatório para atualizar o status."},
                status=400,
            )

        # Chama a função de atualização no serviço de produção
        status_code, mensagem, data = OrdemProducaoService().atualizar_status(
            ordem_producao, novo_status, usuario_id
        )

        # Verifica os diferentes códigos de status retornados pelo serviço
        if status_code == 404:
            return Response({"mensagem": mensagem}, status=404)

        if status_code == 200:
            return Response(data, status=200)

        # Caso ocorra algum erro, retorna com status 409 e mensagem de erro
        return Response({"mensagem": mensagem}, status=409)
