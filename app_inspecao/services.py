from django.db import connections, transaction, IntegrityError


class OrdemProducaoService:

    def obter_ordem_inspecao(self, ordem_producao):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    KPI.ORDEM_PRODUCAO,
                    KPI.PRODUTO,
                    KPI.STATUS AS STATUS_INSPECAO,
                    KPI.DATA_ABERTURA,
                    KPI.DATA_ALTERACAO,
                    USU_ABE.USERNAME,
                    USU_ALT.USERNAME,
                    KPL.FASE_PRODUCAO,
                    KPL.RECURSO_PRODUTIVO,
                    TRIM(PR.DESC_RECURSO) AS DESC_RECURSO,
					KPL.STATUS AS STATUS_LOTE,
                    TRIM(PF.DESC_FASE_PRODUCAO) AS DESC_FASE_PRODUCAO,
                    KIC.COR_PRODUTO,
                    TRIM(PC.DESC_COR_PRODUTO) AS DESC_COR_PRODUTO,
                    KIC.TOTAL,
                    KIC.AMOSTRA,
                    KIC.STATUS AS STATUS_COR
                FROM
                    KING_PRODUCAO_INSPECAO KPI
                    INNER JOIN
                        AUTH_USER USU_ABE ON USU_ABE.ID = KPI.USUARIO_ABERTURA
                    LEFT JOIN
                        AUTH_USER USU_ALT ON USU_ALT.ID = KPI.USUARIO_ALTERACAO
                    INNER JOIN 
                        KING_INSPECAO_LOTE KPL ON KPL.ORDEM_PRODUCAO = KPI.ORDEM_PRODUCAO
                    INNER JOIN
                        PRODUCAO_FASE PF ON PF.FASE_PRODUCAO = KPL.FASE_PRODUCAO
                    INNER JOIN
                        PRODUCAO_RECURSOS PR ON PR.RECURSO_PRODUTIVO = KPL.RECURSO_PRODUTIVO
                    INNER JOIN KING_INSPECAO_COR KIC ON KIC.ORDEM_PRODUCAO = KPL.ORDEM_PRODUCAO 
                        AND KIC.RECURSO_PRODUTIVO = KPL.RECURSO_PRODUTIVO
                        AND KIC.FASE_PRODUCAO = KPL.FASE_PRODUCAO
                    INNER JOIN PRODUTO_CORES PC ON PC.COR_PRODUTO = KIC.COR_PRODUTO
                        AND PC.PRODUTO = KPI.PRODUTO
                WHERE
                    KPI.ORDEM_PRODUCAO = %s
                """,
                [ordem_producao],
            )
            rows = cursor.fetchall()

        if not rows:
            return None

        # Processando os dados retornados da consulta
        result = self.processar_ordem(rows)
        # Serializando o resultado
        return result

    def obter_ordem_producao(self, ordem_producao):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    TRIM(PT.ordem_producao) AS ORDEM_PRODUCAO,
                    TRIM(PTS.PRODUTO) AS PRODUTO,
                    NULL AS STATUS_INSPECAO,
                    NULL AS DATA_ABERTURA,  
                    NULL AS DATA_ALTERACAO,  
                    NULL AS USUARIO_ABERTURA, 
                    NULL AS USUARIO_ALTERACAO,  
                    TRIM(PT.fase_producao) AS FASE_PRODUCAO,
                    TRIM(PT.recurso_produtivo) AS RECURSO_PRODUTIVO,
                    TRIM(PR.desc_recurso) AS DESC_RECURSO,
					NULL AS STATUS_LOTE,  
                    TRIM(PF.desc_fase_producao) AS DESC_FASE_PRODUCAO,
                    TRIM(PTS.cor_produto) AS COR_PRODUTO,
                    TRIM(PC.desc_cor_produto) AS DESC_COR_PRODUTO,
                    PTS.qtde_s AS TOTAL,
                    NULL AS AMOSTRA,  
                    NULL AS STATUS_COR  
                FROM producao_tarefas PT
                    INNER JOIN 
                        producao_fase PF ON PF.fase_producao = PT.fase_producao
                    INNER JOIN 
                        producao_recursos PR ON PR.recurso_produtivo = PT.recurso_produtivo
                    INNER JOIN producao_tarefas_saldo PTS ON PTS.ordem_producao = PT.ordem_producao
                        AND PTS.tarefa = PT.tarefa
                    INNER JOIN produto_cores PC ON PC.produto = PTS.produto
                        AND PC.cor_produto = PTS.cor_produto
                WHERE PT.ORDEM_PRODUCAO = %s
                    AND PT.QTDE_EM_PROCESSO > 0
                    """,
                [ordem_producao],
            )
            rows = cursor.fetchall()

        if not rows:
            return None

        # Processando os dados retornados da consulta
        result = self.processar_ordem(rows)

        # Serializando o resultado
        return result

    def processar_ordem(self, rows):
        lotes = {}

        for row in rows:
            # Captura dos valores conforme os índices identificados
            ordem_producao = row[0]
            produto = row[1]
            status_inspecao = row[2]
            data_abertura = row[3]
            data_alteracao = row[4]
            usuario_abertura = row[5]
            usuario_alteracao = row[6]
            fase_producao = row[7]
            recurso_produtivo = row[8]
            desc_recurso = row[9]
            status_lote = row[10] if row[10] is not None else "Pendente"
            desc_fase_producao = row[11]
            cor_produto = row[12]
            desc_cor_produto = row[13]
            total = row[14]
            amostra = row[15] if row[15] is not None else self.calcular_amostra(total)
            status_cor = row[16] if row[16] is not None else "Pendente"

            # Montando o lote
            if recurso_produtivo not in lotes:
                lotes[recurso_produtivo] = {
                    "recurso_produtivo": recurso_produtivo,
                    "fase_producao": fase_producao,
                    "desc_recurso": desc_recurso,
                    "status": status_lote,  # Adiciona o status do lote diretamente
                    "desc_fase_producao": desc_fase_producao,
                    "total": 0,
                    "cores": [],
                }

            # Soma o total de cada cor do lote para obter o total do lote
            lotes[recurso_produtivo]["total"] += total

            # Monta a cor
            cor_produto_dict = {
                "cor_produto": cor_produto,
                "desc_cor_produto": desc_cor_produto,
                "total": total,
                "amostra": amostra,
                "status": status_cor,
            }

            # Adiciona a cor ao lote correspondente
            lotes[recurso_produtivo]["cores"].append(cor_produto_dict)

        # Monta o resultado final, adicionando campos de forma explícita
        result = {
            "ordem_producao": ordem_producao,
            "status": status_inspecao,
            "data_abertura": data_abertura,
            "data_alteracao": data_alteracao,
            "usuario_abertura": usuario_abertura,
            "usuario_alteracao": usuario_alteracao,
            "produto": produto,
            "lotes": list(lotes.values()),
        }

        # Adicione chaves opcionais apenas se não forem None

        return result

    def calcular_amostra(self, total):
        criterios = [
            {"min": 2, "max": 8, "amostra": 2},
            {"min": 9, "max": 15, "amostra": 3},
            {"min": 16, "max": 25, "amostra": 5},
            {"min": 26, "max": 50, "amostra": 8},
            {"min": 51, "max": 90, "amostra": 13},
            {"min": 91, "max": 150, "amostra": 20},
            {"min": 151, "max": 280, "amostra": 32},
            {"min": 281, "max": 500, "amostra": 50},
            {"min": 501, "max": 1200, "amostra": 80},
            {"min": 1201, "max": 3200, "amostra": 125},
            {"min": 3201, "max": 10000, "amostra": 200},
            {"min": 10001, "max": 35000, "amostra": 315},
        ]

        for criterio in criterios:
            if criterio["min"] <= total <= criterio["max"]:
                return criterio["amostra"]

        return total  # Se não se encaixar em nenhum critério, retorna o próprio total

    def criar_inspecao(self, ordem_producao, usuario_id):
        ordem_data = self.obter_ordem_producao(ordem_producao)

        if not ordem_data:
            return (None, "Ordem de produção não encontrada.", None)

        produto = ordem_data.get("produto")

        if not produto:
            return (None, "Produto não encontrado nos dados da ordem.", None)

        try:
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1 FROM KING_PRODUCAO_INSPECAO 
                    WHERE ORDEM_PRODUCAO = %s AND PRODUTO = %s
                    """,
                    [ordem_producao, produto],
                )
                inspecao_existente = cursor.fetchone()

            if inspecao_existente:
                return (False, "Já existe inspeção para esta ordem de produção", None)
        except Exception as e:
            return (False, f"Erro ao verificar existência da inspeção: {str(e)}", None)

        try:
            with transaction.atomic():
                # Criar registro na tabela KING_PRODUCAO_INSPECAO sem DATA_ALTERACAO e USUARIO_ALTERACAO
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO KING_PRODUCAO_INSPECAO 
                        (ORDEM_PRODUCAO, PRODUTO, STATUS, DATA_ABERTURA, USUARIO_ABERTURA) 
                        VALUES (%s, %s, %s, GETDATE(), %s)
                        """,
                        [ordem_producao, produto, "Pendente", usuario_id],
                    )

                # Inserir registros nas tabelas KING_INSPECAO_LOTE e KING_INSPECAO_COR
                for fase in ordem_data["lotes"]:
                    fase_producao = fase["fase_producao"]
                    recurso_produtivo = fase["recurso_produtivo"]
                    total = fase["total"]

                    # Inserir na tabela KING_INSPECAO_LOTE com a coluna STATUS
                    with connections["default"].cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO KING_INSPECAO_LOTE
                            (FASE_PRODUCAO, RECURSO_PRODUTIVO, TOTAL, ORDEM_PRODUCAO, STATUS)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            [
                                fase_producao,
                                recurso_produtivo,
                                total,
                                ordem_producao,
                                "Pendente",
                            ],
                        )

                    # Inserir na tabela KING_INSPECAO_COR
                    for cor in fase["cores"]:
                        cor_produto = cor["cor_produto"]
                        amostra = cor["amostra"]
                        total_cor = cor["total"]
                        status = cor["status"]

                        # Inserir na tabela KING_INSPECAO_COR com todas as colunas requeridas
                        with connections["default"].cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO KING_INSPECAO_COR
                                (COR_PRODUTO, FASE_PRODUCAO, TOTAL, AMOSTRA, STATUS, ORDEM_PRODUCAO, RECURSO_PRODUTIVO)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """,
                                [
                                    cor_produto,
                                    fase_producao,
                                    total_cor,
                                    amostra,
                                    status,
                                    ordem_producao,
                                    recurso_produtivo,
                                ],
                            )
                ordem_data = self.obter_ordem_inspecao(ordem_producao)
                return (True, "Inspeção criada com sucesso.", ordem_data)
        except Exception as e:
            return (False, f"Erro ao criar inspeção: {str(e)}", None)

    def excluir_inspecao(self, ordem_producao):
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1 FROM KING_PRODUCAO_INSPECAO 
                    WHERE ORDEM_PRODUCAO = %s
                    """,
                    [ordem_producao],
                )
                inspecao_existente = cursor.fetchone()

            if not inspecao_existente:
                return (
                    404,
                    "Inspeção não encontrada para a ordem de produção fornecida.",
                    None,
                )
            with transaction.atomic():
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM KING_PRODUCAO_INSPECAO 
                        WHERE ORDEM_PRODUCAO = %s
                        """,
                        [ordem_producao],
                    )
                ordem_data = self.obter_ordem_producao(ordem_producao)
            return (200, "Inspeção excluída com sucesso.", ordem_data)

        except Exception as e:
            return (409, f"Erro ao excluir a inspeção: {str(e)}", None)

    def atualizar_status(self, ordem_producao, novo_status, usuario_id):
        try:
            with connections["default"].cursor() as cursor:
                # Verifica se a inspeção existe
                cursor.execute(
                    """
                    SELECT 1 FROM KING_PRODUCAO_INSPECAO 
                    WHERE ORDEM_PRODUCAO = %s
                    """,
                    [ordem_producao],
                )
                inspecao_existente = cursor.fetchone()

            if not inspecao_existente:
                return (
                    404,
                    "Inspeção não encontrada para a ordem de produção fornecida.",
                    None,
                )

            # Validação para status 'Encerrada'
            if novo_status == 'Encerrada':
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT 1 FROM KING_INSPECAO_LOTE 
                        WHERE ORDEM_PRODUCAO = %s AND STATUS != 'Finalizado'
                        """,
                        [ordem_producao],
                    )
                    lote_nao_finalizado = cursor.fetchone()

                if lote_nao_finalizado:
                    return (
                        409,
                        "Não é possível encerrar a inspeção pois existem lotes não finalizados.",
                        None,
                    )

            # Atualiza o status se passar a validação
            with transaction.atomic():
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE KING_PRODUCAO_INSPECAO 
                        SET STATUS = %s,
                            DATA_ALTERACAO = GETDATE(),
                            USUARIO_ALTERACAO = %s
                        WHERE ORDEM_PRODUCAO = %s
                        """,
                        [novo_status, usuario_id, ordem_producao],
                    )

                    cursor.execute(
                        """
                        SELECT DATA_ALTERACAO
                        FROM KING_PRODUCAO_INSPECAO
                        WHERE ORDEM_PRODUCAO = %s
                        """,
                        [ordem_producao],
                    )
                    data_alteracao_atualizada = cursor.fetchone()[0]

            result = {
                "data_alteracao": data_alteracao_atualizada,
            }

            return (
                200,
                "Inspeção Atualizada com sucesso",
                result,
            )

        except Exception as e:
            return (409, f"Erro ao atualizar o status: {str(e)}", None)

