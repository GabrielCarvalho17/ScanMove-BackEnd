from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import connections
from .serializers import MateriaisSerializer, LocalizacoesSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter

class PecaViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id='obter_peca',
        parameters=[
            OpenApiParameter(name="peca", type=OpenApiTypes.STR, location=OpenApiParameter.PATH),
        ],
        responses={200: MateriaisSerializer(many=True)}
    )
    def obter_peca(self, request, peca=None):
        if not peca:
            return Response({'detail': 'Peca é obrigatória.'}, status=400)

        with connections['default'].cursor() as cursor:
            cursor.execute('''
                SELECT 
                    e.peca,
                    e.partida,
                    e.filial,
                    e.localizacao,
                    e.material,
                    m.desc_material,
                    mc.cor_material,
                    mc.desc_cor_material,
                    m.unid_estoque,
                    e.qtde
                FROM 
                    ESTOQUE_MAT_PECA e
                JOIN 
                    MATERIAIS m ON e.material = m.material
                LEFT JOIN 
                    MATERIAIS_LOCALIZA l ON e.localizacao = l.localizacao
                JOIN 
                    MATERIAIS_CORES mc ON mc.MATERIAL = e.MATERIAL AND mc.COR_MATERIAL = e.COR_MATERIAL
                WHERE
                    l.localizacao is not null 
                AND e.PECA is not null 
                AND e.PECA <> '' 
                AND e.qtde > 0
                AND e.PECA = %s
            ''', [peca])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if not results:
            return Response({'detail': 'Not found.'}, status=404)

        total = len(results)
        serializer = MateriaisSerializer(results, many=True)
        return Response({'total': total, 'results': serializer.data})


class LocalizacaoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id='obter_localizacao',
        parameters=[OpenApiParameter(name="localizacao", type=OpenApiTypes.STR, location=OpenApiParameter.PATH)],
        responses={200: LocalizacoesSerializer(many=True)}
    )
    def obter_localizacao(self, request, localizacao=None):
        if not localizacao:
            return Response({'detail': 'Not found.'}, status=404)

        with connections['default'].cursor() as cursor:
            cursor.execute('''
                SELECT 
                    l.localizacao, 
                    l.filial
                FROM 
                    MATERIAIS_LOCALIZA l 
                WHERE 
                    l.localizacao = %s
            ''', [localizacao])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if not results:
            return Response({'detail': 'Not found.'}, status=404)

        total = len(results)
        serializer = LocalizacoesSerializer(results, many=True)
        return Response({'total': total, 'results': serializer.data})
