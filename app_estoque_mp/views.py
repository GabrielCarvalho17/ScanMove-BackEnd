from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import connections
from .serializers import MateriaisSerializer, LocalizacoesSerializer, MovimentacaoSerializer
from django.db import transaction, IntegrityError
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


from rest_framework import viewsets
from rest_framework.response import Response
from django.db import transaction, connections, IntegrityError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

class MovimentacaoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id='listar_movimentacoes',
        responses={200: MovimentacaoSerializer(many=True)}
    )
    def listar_movimentacoes(self, request):
        movimentacoes_query = '''
            SELECT 
                m.movimentacao,
                m.data_inicio,
                m.data_modificacao,
                m.status,
                m.usuario,
                m.origem,
                loc_origem.filial AS filial_origem,
                m.destino,
                loc_destino.filial AS filial_destino,
                m.total_pecas
            FROM 
                KING_ESTOQUE_MAT_MOV m
            LEFT JOIN 
                MATERIAIS_LOCALIZA loc_origem ON m.origem = loc_origem.localizacao
            LEFT JOIN 
                MATERIAIS_LOCALIZA loc_destino ON m.destino = loc_destino.localizacao
        '''

        itens_query = '''
            SELECT 
                i.movimentacao,
                i.peca,
                i.partida,
                i.material,
                mat.desc_material,
                i.cor_material,
                mc.desc_cor_material,
                i.unidade,
                i.quantidade
            FROM 
                KING_ESTOQUE_MAT_MOV_ITEM i
            LEFT JOIN 
                MATERIAIS mat ON i.material = mat.material
            LEFT JOIN 
                MATERIAIS_CORES mc ON i.material = mc.material AND i.cor_material = mc.cor_material
        '''

        with connections['default'].cursor() as cursor:
            # Executar a query das movimentações com junção
            cursor.execute(movimentacoes_query)
            movimentacoes_columns = [col[0] for col in cursor.description]
            movimentacoes_results = [dict(zip(movimentacoes_columns, row)) for row in cursor.fetchall()]

            # Executar a query dos itens
            cursor.execute(itens_query)
            itens_columns = [col[0] for col in cursor.description]
            itens_results = [dict(zip(itens_columns, row)) for row in cursor.fetchall()]

        movimentacoes = {}
        for mov in movimentacoes_results:
            movimentacoes[mov['movimentacao']] = {
                'movimentacao': mov['movimentacao'],
                'data_inicio': mov['data_inicio'],
                'data_modificacao': mov['data_modificacao'],
                'status': mov['status'],
                'usuario': mov['usuario'],
                'origem': mov['origem'],
                'filial_origem': mov['filial_origem'],
                'destino': mov['destino'],
                'filial_destino': mov['filial_destino'],
                'total_pecas': mov['total_pecas'],
                'itens': []
            }

        for item in itens_results:
            movimentacoes[item['movimentacao']]['itens'].append({
                'peca': item['peca'],
                'partida': item['partida'],
                'material': item['material'],
                'desc_material': item['desc_material'],
                'cor_material': item['cor_material'],
                'desc_cor_material': item['desc_cor_material'],
                'unidade': item['unidade'],
                'quantidade': item['quantidade']
            })

        movimentacoes_list = list(movimentacoes.values())
        serializer = MovimentacaoSerializer(movimentacoes_list, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id='obter_movimentacao',
        parameters=[
            OpenApiParameter(name="movimentacao", type=OpenApiTypes.INT, location=OpenApiParameter.PATH),
        ],
        responses={200: MovimentacaoSerializer(many=False)}
    )
    
    def obter_movimentacao(self, request, movimentacao=None):
        if not movimentacao:
            return Response({'detail': 'Movimentação é obrigatória.'}, status=400)

        movimentacao_query = '''
            SELECT 
                m.movimentacao,
                m.data_inicio,
                m.data_modificacao,
                m.status,
                m.usuario,
                m.origem,
                loc_origem.filial AS filial_origem,
                m.destino,
                loc_destino.filial AS filial_destino,
                m.total_pecas
            FROM 
                KING_ESTOQUE_MAT_MOV m
            LEFT JOIN 
                MATERIAIS_LOCALIZA loc_origem ON m.origem = loc_origem.localizacao
            LEFT JOIN 
                MATERIAIS_LOCALIZA loc_destino ON m.destino = loc_destino.localizacao
            WHERE 
                m.movimentacao = %s
        '''

        itens_query = '''
            SELECT 
                i.peca,
                i.partida,
                i.material,
                mat.desc_material,
                i.cor_material,
                mc.desc_cor_material,
                i.unidade,
                i.quantidade
            FROM 
                KING_ESTOQUE_MAT_MOV_ITEM i
            LEFT JOIN 
                MATERIAIS mat ON i.material = mat.material
            LEFT JOIN 
                MATERIAIS_CORES mc ON i.material = mc.material AND i.cor_material = mc.cor_material
            WHERE 
                i.movimentacao = %s
        '''

        with connections['default'].cursor() as cursor:
            # Executar a query da movimentação com junção
            cursor.execute(movimentacao_query, [movimentacao])
            movimentacao_data = cursor.fetchone()
            if not movimentacao_data:
                return Response({'detail': 'Movimentação não encontrada.'}, status=404)

            movimentacao_columns = [col[0] for col in cursor.description]
            movimentacao_dict = dict(zip(movimentacao_columns, movimentacao_data))

            # Executar a query dos itens da movimentação específica
            cursor.execute(itens_query, [movimentacao])
            itens_columns = [col[0] for col in cursor.description]
            itens_results = [dict(zip(itens_columns, row)) for row in cursor.fetchall()]

        movimentacao_dict['itens'] = [
            {
                'peca': item['peca'],
                'partida': item['partida'],
                'material': item['material'],
                'desc_material': item['desc_material'],
                'cor_material': item['cor_material'],
                'desc_cor_material': item['desc_cor_material'],
                'unidade': item['unidade'],
                'quantidade': item['quantidade']
            }
            for item in itens_results
        ]

        serializer = MovimentacaoSerializer(movimentacao_dict)
        return Response(serializer.data)


    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id='criar_movimentacao',
        request=MovimentacaoSerializer,
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def criar_movimentacao(self, request):
        serializer = MovimentacaoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        try:
            with transaction.atomic():
                with connections['default'].cursor() as cursor:
                    # Inserir a movimentação e obter o ID usando OUTPUT INSERTED
                    cursor.execute('''
                        INSERT INTO KING_ESTOQUE_MAT_MOV (
                            data_inicio, data_modificacao, status, usuario,
                            origem, destino, total_pecas
                        ) 
                        OUTPUT INSERTED.MOVIMENTACAO
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', [
                        data['data_inicio'], data['data_modificacao'], data['status'], data['usuario'],
                        data['origem'], data.get('destino'), data['total_pecas']
                    ])
                    movimentacao_id = cursor.fetchone()[0]

                    # Insere os itens relacionados à movimentação
                    for item in data.get('itens', []):
                        cursor.execute('''
                            INSERT INTO KING_ESTOQUE_MAT_MOV_ITEM (
                                movimentacao, peca, partida, material, cor_material,
                                unidade, quantidade
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ''', [
                            movimentacao_id, item['peca'], item['partida'], item['material'], item['cor_material'],
                            item['unidade'], item['quantidade']
                        ])

            return Response({'id_sqlite': movimentacao_id, 'status': 'sucesso'}, status=201)

        except IntegrityError as e:
            return Response({'detail': str(e)}, status=400)

        except Exception as e:
            return Response({'detail': str(e)}, status=500)




  