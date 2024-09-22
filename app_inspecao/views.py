from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import connections
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .serializers import (
    OrdemInspecaoSerializer,
    OrdemProducaoSerializer,
)


class OrdemProducaoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Inspeção"],
        operation_id="obter_ordem",
        parameters=[
            OpenApiParameter(
                name="ordem_producao",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,  # Mudando de QUERY para PATH
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Ordem de produção encontrada com sucesso.",
                response=OrdemInspecaoSerializer,
            ),
            404: OpenApiResponse(description="Ordem de produção não encontrada."),
            500: OpenApiResponse(description="Erro interno do servidor"),
        },
    )
    def obter_ordem(self, request, ordem_producao):
        if not ordem_producao:
            return Response({"detail": "Ordem de produção é obrigatória."}, status=400)

        # Primeiro, tentar obter os dados da ordem de inspeção pela ordem de produção
        resultado_inspecao = self.obter_ordem_inspecao(ordem_producao)
        if resultado_inspecao is not None:
            return Response(resultado_inspecao, status=200)

        # Se a ordem de inspeção não for encontrada, tenta obter a ordem de produção
        resultado_producao = self.obter_ordem_producao(ordem_producao)
        if resultado_producao is not None:
            return Response(resultado_producao, status=200)

        # Se nada for encontrado, retorna uma mensagem de erro
        return Response({"detail": "Ordem não encontrada."}, status=404)

    def obter_ordem_inspecao(self, ordem_producao):
        # Aqui, a consulta será feita usando ordem_producao
        if not ordem_producao:
            return None

        # Executando a consulta para obter os dados da ordem de inspeção com base na ordem de produção
        with connections["default"].cursor() as cursor:
            # Executando a query SQL
            cursor.execute(
                """
                SELECT 
                    KPI.ORDEM_PRODUCAO,
                    KPI.ORDEM_INSPECAO,
                    KPI.PRODUTO,
                    KPI.STATUS,
                    KPI.DATA_ABERTURA,
                    KPI.DATA_ALTERACAO,
                    AU1.USERNAME AS USUARIO_ABERTURA,
                    AU2.USERNAME AS USUARIO_ALTERACAO,
                    KPF.FASE_PRODUCAO,
                    PF.DESC_FASE_PRODUCAO,
                    KPF.RECURSO_PRODUTIVO,
                    PR.DESC_RECURSO,
                    KPF.TOTAL
                FROM 
                    KING_PRODUCAO_INSPECAO KPI
                    INNER JOIN KING_INSPECAO_FASE KPF ON KPF.ORDEM_INSPECAO = KPI.ORDEM_INSPECAO
                    INNER JOIN PRODUCAO_FASE PF ON PF.FASE_PRODUCAO = KPF.FASE_PRODUCAO
                    INNER JOIN PRODUCAO_RECURSOS PR ON PR.RECURSO_PRODUTIVO = KPF.RECURSO_PRODUTIVO
                    -- Junção para trazer o nome do USUARIO_ABERTURA
                    INNER JOIN AUTH_USER AU1 ON AU1.ID = KPI.USUARIO_ABERTURA
                    -- Junção para trazer o nome do USUARIO_ALTERACAO
                    LEFT JOIN AUTH_USER AU2 ON AU2.ID = KPI.USUARIO_ALTERACAO
                WHERE  KPI.ORDEM_PRODUCAO = %s
                """,
                [ordem_producao],
            )
            rows = cursor.fetchall()

            if not rows:
                return None

            # Processando as linhas de resultado
            result = {
                "ordem_producao": rows[0][0],
                "ordem_inspecao": rows[0][1],
                "produto": rows[0][2],
                "status": rows[0][3],
                "data_abertura": rows[0][4],
                "data_encerramento": rows[0][5],
                "usuario_abertura": rows[0][6],  
                "usuario_alteracao": rows[0][7],
                "fases": [],
            }

            # Adicionando fases da produção para cada linha
            for row in rows:
                fase = {
                    "fase_producao": row[8],
                    "desc_fase_producao": row[9],
                    "recurso_produtivo": row[10],
                    "desc_recurso": row[11],
                    "qtde_em_processo": row[12],
                }
                result["fases"].append(fase)

            # Serializando o resultado final
            serializer = OrdemInspecaoSerializer(result)
            return serializer.data


    def obter_ordem_producao(self, ordem_producao):
        # Aqui também a consulta será feita usando ordem_producao
        if not ordem_producao:
            return None

        # Executando a consulta para obter os dados da ordem de produção
        with connections["default"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    Trim(pt.fase_producao) AS fase_producao, 
                    Trim(pf.desc_fase_producao) AS desc_fase_producao, 
                    pt.qtde_em_processo, 
                    pt.ordem_producao
                FROM 
                    producao_tarefas pt
                INNER JOIN 
                    producao_fase pf ON pf.fase_producao = pt.fase_producao
                WHERE 
                    pt.ordem_producao = %s 
                    AND pt.qtde_em_processo > 0
                """,
                [ordem_producao],
            )
            rows = cursor.fetchall()

        if not rows:
            return None

        # Organize os resultados para serialização
        fases = []
        ordem_producao_value = rows[0][
            3
        ]  # Todas as linhas têm a mesma ordem de produção

        for row in rows:
            fases.append(
                {
                    "fase_producao": row[0],
                    "desc_fase_producao": row[1],
                    "qtde_em_processo": row[2],
                }
            )

        # Formatar os dados para serialização
        result = {"ordem_producao": ordem_producao_value, "fases": fases}

        # Serializando o resultado final
        serializer = OrdemProducaoSerializer(result)
        return serializer.data


