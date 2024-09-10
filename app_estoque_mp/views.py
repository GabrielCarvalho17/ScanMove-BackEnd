from collections import defaultdict
from datetime import datetime
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import connections, transaction, IntegrityError
from .serializers import (
    AtualizarMovimentacaoSerializer,
    IncluiPecasSerializer,
    LocalizacoesSerializer,
    MovimentacaoSerializer,
    PecaSerializer,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


class PecaViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="obter_peca",
        parameters=[
            OpenApiParameter(
                name="peca", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
            ),
        ],
        responses={200: PecaSerializer()},  # Não usar many=True aqui
    )
    def obter_peca(self, request, peca=None):
        if not peca:
            return Response({"detail": "Peca é obrigatória."}, status=400)

        with connections["default"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    e.peca,
                    e.partida,
                    e.filial, 
                    e.localizacao,
                    e.material,
                    m.desc_material,
                    mc.cor_material,
                    mc.desc_cor_material,
                    m.unid_estoque AS unidade,  
                    e.qtde AS quantidade         
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
            """,
                [peca],
            )
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            result = dict(zip(columns, row)) if row else None

        if not result:
            return Response({"detail": "Not found."}, status=404)

        serializer = PecaSerializer(result)  # Não usar many=True aqui
        return Response(serializer.data)


class LocalizacaoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="obter_localizacao",
        parameters=[
            OpenApiParameter(
                name="localizacao",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
            )
        ],
        responses={200: LocalizacoesSerializer()},
    )
    def obter_localizacao(self, request, localizacao=None):
        if not localizacao:
            return Response({"detail": "Not found."}, status=404)

        with connections["default"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    l.localizacao, 
                    l.filial
                FROM 
                    MATERIAIS_LOCALIZA l 
                WHERE 
                    l.localizacao = %s
            """,
                [localizacao],
            )
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if not results:
            return Response({"detail": "Not found."}, status=404)

        # Retornar apenas o primeiro item da lista de resultados
        serializer = LocalizacoesSerializer(results[0])
        return Response(serializer.data)


class MovimentacaoViewSet(viewsets.ViewSet):
    serializer_class = MovimentacaoSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="listar_movimentacoes",
        responses={200: MovimentacaoSerializer(many=True)},
    )
    def listar_movimentacoes(self, request):
        username = request.user.username  # Obtém o username do usuário autenticado
        data_atual = datetime.now().strftime(
            "%Y-%m-%d"
        )  # Obtém a data atual no formato YYYY-MM-DD

        query = f"""
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
                m.total_pecas,
                mp.peca,
                mp.partida,
                mp.material,
                mat.desc_material,
                mp.cor_material,
                mc.desc_cor_material,
                mp.unidade,
                mp.quantidade,
                ep.localizacao, 
                ep.filial
            FROM 
                dbo.KING_ESTOQUE_MAT_MOV m
            LEFT JOIN 
                MATERIAIS_LOCALIZA loc_origem ON m.origem = loc_origem.localizacao
            LEFT JOIN 
                MATERIAIS_LOCALIZA loc_destino ON m.destino = loc_destino.localizacao
            LEFT JOIN 
                dbo.KING_ESTOQUE_MAT_MOV_PECA mp ON m.movimentacao = mp.movimentacao
            LEFT JOIN 
                MATERIAIS mat ON mp.material = mat.material
            LEFT JOIN 
                MATERIAIS_CORES mc ON mp.material = mc.material AND mp.cor_material = mc.cor_material
            LEFT JOIN 
                ESTOQUE_MAT_PECA ep ON ep.PECA = mp.PECA
            WHERE 
                m.USUARIO = '{username}' 
                AND (
                    CONVERT(DATE, m.DATA_INICIO) = '{data_atual}'  -- Movimentações do dia atual
                    OR m.status = 'Andamento'                      -- Ou movimentações em andamento
                )
            ORDER BY 
                m.status
        """

        with connections["default"].cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Estrutura para armazenar as movimentações
        movimentacoes = defaultdict(
            lambda: {
                "movimentacao": None,
                "data_inicio": None,
                "data_modificacao": None,
                "status": None,
                "usuario": None,
                "origem": None,
                "destino": None,
                "total_pecas": None,
                "filial_origem": None,
                "filial_destino": None,
                "pecas": [],
            }
        )

        # Preenchimento das movimentações e suas respectivas peças
        for result in results:
            mov_id = result["movimentacao"]
            if movimentacoes[mov_id]["movimentacao"] is None:
                movimentacoes[mov_id].update(
                    {
                        "movimentacao": result["movimentacao"],
                        "data_inicio": result["data_inicio"],
                        "data_modificacao": result["data_modificacao"],
                        "status": result["status"],
                        "usuario": result["usuario"],
                        "origem": result["origem"],
                        "destino": result["destino"],
                        "total_pecas": result["total_pecas"],
                        "filial_origem": result["filial_origem"],
                        "filial_destino": result["filial_destino"],
                    }
                )

            movimentacoes[mov_id]["pecas"].append(
                {
                    "peca": result["peca"],
                    "partida": result["partida"],
                    "material": result["material"],
                    "desc_material": result["desc_material"],
                    "cor_material": result["cor_material"],
                    "desc_cor_material": result["desc_cor_material"],
                    "unidade": result["unidade"],
                    "quantidade": result["quantidade"],
                    "localizacao": result["localizacao"],
                    "filial": result["filial"],
                }
            )

        movimentacoes_list = list(movimentacoes.values())
        serializer = MovimentacaoSerializer(movimentacoes_list, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="obter_movimentacao",
        responses={200: MovimentacaoSerializer()},
    )
    def obter_movimentacao(self, request, movimentacao=None):
        username = request.user.username  # Obtém o username do usuário autenticado

        query = """
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
                m.total_pecas,
                mp.peca,
                mp.partida,
                mp.material,
                mat.desc_material,
                mp.cor_material,
                mc.desc_cor_material,
                mp.unidade,
                mp.quantidade,
                ep.localizacao, 
                ep.filial
            FROM 
                dbo.KING_ESTOQUE_MAT_MOV m
            LEFT JOIN 
                MATERIAIS_LOCALIZA loc_origem ON m.origem = loc_origem.localizacao
            LEFT JOIN 
                MATERIAIS_LOCALIZA loc_destino ON m.destino = loc_destino.localizacao
            LEFT JOIN 
                dbo.KING_ESTOQUE_MAT_MOV_PECA mp ON m.movimentacao = mp.movimentacao
            LEFT JOIN 
                MATERIAIS mat ON mp.material = mat.material
            LEFT JOIN 
                MATERIAIS_CORES mc ON mp.material = mc.material AND mp.cor_material = mc.cor_material
            LEFT JOIN 
                ESTOQUE_MAT_PECA ep ON ep.PECA = mp.PECA
            WHERE 
                m.USUARIO = %s 
                AND m.movimentacao = %s
        """

        with connections["default"].cursor() as cursor:
            cursor.execute(query, [username, movimentacao])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if not results:
            return Response(
                {"detail": "Movimentação não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        movimentacao = {
            "movimentacao": None,
            "data_inicio": None,
            "data_modificacao": None,
            "status": None,
            "usuario": None,
            "origem": None,
            "destino": None,
            "total_pecas": None,
            "filial_origem": None,
            "filial_destino": None,
            "pecas": [],
        }

        for result in results:
            if movimentacao["movimentacao"] is None:
                movimentacao.update(
                    {
                        "movimentacao": result["movimentacao"],
                        "data_inicio": result["data_inicio"],
                        "data_modificacao": result["data_modificacao"],
                        "status": result["status"],
                        "usuario": result["usuario"],
                        "origem": result["origem"],
                        "destino": result["destino"],
                        "total_pecas": result["total_pecas"],
                        "filial_origem": result["filial_origem"],
                        "filial_destino": result["filial_destino"],
                    }
                )

            movimentacao["pecas"].append(
                {
                    "peca": result["peca"],
                    "partida": result["partida"],
                    "material": result["material"],
                    "desc_material": result["desc_material"],
                    "cor_material": result["cor_material"],
                    "desc_cor_material": result["desc_cor_material"],
                    "unidade": result["unidade"],
                    "quantidade": result["quantidade"],
                    "localizacao": result["localizacao"],
                    "filial": result["filial"],
                }
            )

        serializer = MovimentacaoSerializer(movimentacao)
        return Response(serializer.data)

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="criar_movimentacao",
        request=MovimentacaoSerializer,
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
    )
    def criar_movimentacao(self, request):
        serializer = MovimentacaoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        try:
            with transaction.atomic():
                with connections["default"].cursor() as cursor:
                    # Inserir a movimentação e obter o ID usando OUTPUT INSERTED
                    cursor.execute(
                        """
                        INSERT INTO KING_ESTOQUE_MAT_MOV (
                            data_inicio, data_modificacao, status, usuario,
                            origem, destino, total_pecas
                        ) 
                        OUTPUT INSERTED.MOVIMENTACAO
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                        [
                            data["data_inicio"],
                            data["data_modificacao"],
                            data["status"],
                            data["usuario"],
                            data["origem"],
                            data.get("destino"),
                            data["total_pecas"],
                        ],
                    )
                    movimentacao_id = cursor.fetchone()[0]

                    # Insere os pecas relacionados à movimentação
                    for peca in data.get("pecas", []):
                        cursor.execute(
                            """
                            INSERT INTO KING_ESTOQUE_MAT_MOV_PECA (
                                movimentacao, peca, partida, material, cor_material,
                                unidade, quantidade
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                            [
                                movimentacao_id,
                                peca["peca"],
                                peca["partida"],
                                peca["material"],
                                peca["cor_material"],
                                peca["unidade"],
                                peca["quantidade"],
                            ],
                        )

            return Response(
                {"mov_servidor": movimentacao_id, "status": "sucesso"}, status=201
            )

        except IntegrityError as e:
            return Response({"detail": str(e)}, status=400)

        except Exception as e:
            return Response({"detail": str(e)}, status=500)

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="atualizar_movimentacao",
        request=AtualizarMovimentacaoSerializer,
        parameters=[
            OpenApiParameter(
                name="movimentacao",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Movimentação Atualizada com sucesso."),
            400: OpenApiResponse(description="Erro na atualização"),
            404: OpenApiResponse(description="Movimentação não encontrada"),
            500: OpenApiResponse(description="Erro interno do servidor"),
        },
    )
    def atualizar_movimentacao(self, request, movimentacao=None):
        serializer = AtualizarMovimentacaoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            # Verifica se a movimentação existe e obtém o status, origem e destino atuais
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    "SELECT status, origem, destino FROM KING_ESTOQUE_MAT_MOV WHERE movimentacao = %s",
                    [movimentacao],
                )
                resultado = cursor.fetchone()

                if resultado is None:
                    return Response(
                        {"detail": "Movimentação não encontrada."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                status_atual, origem_atual, destino_atual = resultado

                # Verifica se a movimentação já está finalizada
                if status_atual == "Finalizada":
                    return Response(
                        {
                            "detail": "A movimentação já está finalizada e não pode ser alterada."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Preparando os dados para atualização
                fields_to_update = []
                params = []

                if "origem" in data:
                    fields_to_update.append("origem = %s")
                    params.append(data["origem"])
                if "destino" in data:
                    fields_to_update.append("destino = %s")
                    params.append(data["destino"])
                if "status" in data and data["status"] == True:
                    print("Entrei aqui!")
                    fields_to_update.append("status = %s")
                    params.append("Finalizada")

                    # Atualizar a localizacao em ESTOQUE_MAT_PECA para todas as peças associadas à movimentação
                    try:
                        cursor.execute(
                            """
                            UPDATE ESTOQUE_MAT_PECA
                            SET localizacao = mv.destino
                            FROM ESTOQUE_MAT_PECA ep
                            INNER JOIN KING_ESTOQUE_MAT_MOV_PECA mp ON ep.peca = mp.PECA
                            INNER JOIN KING_ESTOQUE_MAT_MOV mv ON mp.MOVIMENTACAO = mv.MOVIMENTACAO
                            WHERE mv.movimentacao = %s;
                            """,
                            [movimentacao],
                        )
                        logging.info(
                            f"Estoque de materiais atualizado para movimentacao {movimentacao}"
                        )
                    except Exception as e:
                        logging.error(
                            f"Erro ao atualizar o estoque de materiais: {str(e)}"
                        )
                        raise

                # A data_modificacao deve sempre estar presente e ser atualizada
                fields_to_update.append("data_modificacao = %s")
                params.append(data["data_modificacao"])

                if fields_to_update:
                    query = f"""
                        UPDATE KING_ESTOQUE_MAT_MOV
                        SET {', '.join(fields_to_update)}
                        WHERE movimentacao = %s
                    """
                    params.append(movimentacao)
                    cursor.execute(query, params)

            return Response(
                {"detail": "Movimentação atualizada com sucesso."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="excluir_movimentacao",
        parameters=[
            OpenApiParameter(
                name="movimentacao",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
            ),
        ],
        # Removendo a definição explícita de respostas para simplificar a documentação
    )
    def excluir_movimentacao(self, request, movimentacao=None):
        if not movimentacao:
            return Response(
                {"detail": "Movimentação é obrigatória."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with connections["default"].cursor() as cursor:
                # Verifica se a movimentação existe e qual é o seu status
                cursor.execute(
                    """
                    SELECT status FROM KING_ESTOQUE_MAT_MOV WHERE movimentacao = %s
                """,
                    [movimentacao],
                )
                result = cursor.fetchone()

                if not result:
                    return Response(
                        {"detail": "Movimentação não encontrada."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                status_movimentacao = result[0]

                # Verifica se o status é 'Finalizada'
                if status_movimentacao == "Finalizada":
                    return Response(
                        {
                            "detail": "A movimentação já está finalizada e não pode ser excluída."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Exclui a movimentação (pecas relacionados serão excluídos automaticamente)
                cursor.execute(
                    """
                    DELETE FROM KING_ESTOQUE_MAT_MOV WHERE movimentacao = %s
                """,
                    [movimentacao],
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="incluir_pecas",
        request=IncluiPecasSerializer,
        responses={201: None},
    )
    @action(detail=True, methods=["post"], url_path="incluir_pecas")
    def incluir_pecas(self, request, movimentacao=None):
        serializer = IncluiPecasSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pecas_para_incluir = serializer.validated_data.get("pecas", [])
        data_modificacao = serializer.validated_data.get("data_modificacao")

        try:
            with connections["default"].cursor() as cursor:
                # Verifica se a movimentação existe e obtém o status atual
                cursor.execute(
                    "SELECT status FROM KING_ESTOQUE_MAT_MOV WHERE movimentacao = %s",
                    [movimentacao],
                )
                resultado = cursor.fetchone()

                if resultado is None:
                    return Response(
                        {"detail": "Movimentação não encontrada."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                status_atual = resultado[0]

                # Verifica se a movimentação já está finalizada
                if status_atual == "Finalizada":
                    return Response(
                        {
                            "detail": "A movimentação já está finalizada e não pode ser alterada."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Insere as peças especificadas
                for peca in pecas_para_incluir:
                    cursor.execute(
                        """
                        INSERT INTO KING_ESTOQUE_MAT_MOV_PECA (
                            movimentacao, peca, partida, material, cor_material, unidade, quantidade
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            movimentacao,
                            peca["peca"],
                            peca["partida"],
                            peca["material"],
                            peca["cor_material"],
                            peca["unidade"],
                            peca["quantidade"],
                        ],
                    )

                # Atualiza a 'data_modificacao' da movimentação
                cursor.execute(
                    """
                    UPDATE KING_ESTOQUE_MAT_MOV
                    SET data_modificacao = %s
                    WHERE movimentacao = %s
                    """,
                    [data_modificacao, movimentacao],
                )

            return Response(status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=["Estoque de Materiais"],
        operation_id="excluir_pecas",
        responses={204: None},
    )
    @action(
        detail=True,
        methods=["delete"],
        url_path="data_modificacao/(?P<data_modificacao>[^/.]+)/excluir_pecas/(?P<pecas_ids>[^/.]+)",
    )
    def excluir_pecas(
        self, request, movimentacao=None, data_modificacao=None, pecas_ids=None
    ):
        if not data_modificacao:
            return Response(
                {"detail": "Data de modificação não fornecida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not pecas_ids:
            return Response(
                {"detail": "Nenhum ID de peça fornecido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Convertendo os IDs das peças em uma lista de inteiros
        pecas_para_excluir = [int(id) for id in pecas_ids.split(",")]

        try:
            with connections["default"].cursor() as cursor:
                # Verifica se a movimentação existe e obtém o status atual
                cursor.execute(
                    "SELECT status FROM KING_ESTOQUE_MAT_MOV WHERE movimentacao = %s",
                    [movimentacao],
                )
                resultado = cursor.fetchone()

                if resultado is None:
                    return Response(
                        {"detail": "Movimentação não encontrada."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                status_atual = resultado[0]

                # Verifica se a movimentação já está finalizada
                if status_atual == "Finalizada":
                    return Response(
                        {
                            "detail": "A movimentação já está finalizada e não pode ser alterada."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Atualiza a 'data_modificacao' da movimentação
                cursor.execute(
                    """
                    UPDATE KING_ESTOQUE_MAT_MOV
                    SET data_modificacao = %s
                    WHERE movimentacao = %s
                    """,
                    [data_modificacao, movimentacao],
                )

                # Deleta as peças especificadas
                placeholders = ", ".join(
                    ["%s"] * len(pecas_para_excluir)
                )  # Cria placeholders %s,%s,%s,...
                sql = f"""
                    DELETE FROM KING_ESTOQUE_MAT_MOV_PECA 
                    WHERE movimentacao = %s AND peca IN ({placeholders})
                """
                params = [movimentacao] + pecas_para_excluir
                cursor.execute(sql, params)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
