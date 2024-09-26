from django.db import connections, transaction, IntegrityError


class OrdemProducaoService:

    def obter_ordem_inspecao(self, ordem_producao):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    KPI.ORDEM_PRODUCAO,
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
                    INNER JOIN KING_INSPECAO_LOTE KPF ON KPF.ORDEM_PRODUCAO = KPI.ORDEM_PRODUCAO
                    INNER JOIN PRODUCAO_FASE PF ON PF.FASE_PRODUCAO = KPF.FASE_PRODUCAO
                    INNER JOIN PRODUCAO_RECURSOS PR ON PR.RECURSO_PRODUTIVO = KPF.RECURSO_PRODUTIVO
                    INNER JOIN AUTH_USER AU1 ON AU1.ID = KPI.USUARIO_ABERTURA
                    LEFT JOIN AUTH_USER AU2 ON AU2.ID = KPI.USUARIO_ALTERACAO
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
                        TRIM(PT.ordem_producao),
                        TRIM(PT.fase_producao),
                        TRIM(PF.desc_fase_producao),
                        TRIM(PR.desc_recurso),
                        TRIM(PT.recurso_produtivo),
                        TRIM(PTS.cor_produto),
                        TRIM(PC.desc_cor_produto),
                        PTS.qtde_s as total,
                        TRIM(PTS.PRODUTO)
                    FROM   producao_tarefas PT
                        INNER JOIN producao_fase PF ON PF.fase_producao = PT.fase_producao
                        INNER JOIN producao_recursos PR ON PR.recurso_produtivo = PT.recurso_produtivo
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
            fase_producao = row[1]
            recurso_produtivo = row[4]  # Recurso produtivo agora faz parte da chave
            
            # Criando uma chave única para fase + recurso_produtivo
            fase_recurso_key = f"{fase_producao}_{recurso_produtivo}"
            
            if fase_recurso_key not in lotes:
                lotes[fase_recurso_key] = {
                    "recurso_produtivo": recurso_produtivo,
                    "fase_producao": fase_producao,
                    "desc_recurso": row[3],
                    "desc_fase_producao": row[2],
                    "total": 0,
                    "cores": [],
                }
            
            # Atualizando o total da fase + recurso
            lotes[fase_recurso_key]["total"] += row[7]

            # Calculando amostra
            amostra = self.calcular_amostra(row[7])

            # Adicionando a cor
            cor_produto = {
                "cor_produto": row[5],
                "desc_cor_produto": row[6],
                "total": row[7],
                "amostra": amostra,
            }
            lotes[fase_recurso_key]["cores"].append(cor_produto)

        # Retornando o resultado com as lotes e lotes devidamente separados
        result = {
            "ordem_producao": rows[0][0], 
            "produto": rows[0][8],  # Ajuste se necessário conforme o índice correto do produto
            "lotes": list(lotes.values())  # Retornando apenas os valores das lotes com recurso
        }
        
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

        produto = ordem_data.get("produto")  # Pegando o valor de 'produto' de ordem_data
        if not produto:
            return (None, "Produto não encontrado nos dados da ordem.", None)

        try:
            with transaction.atomic():
                # Criar registro na tabela KING_PRODUCAO_INSPECAO
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO KING_PRODUCAO_INSPECAO 
                        (ORDEM_PRODUCAO, PRODUTO, STATUS, DATA_ABERTURA, DATA_ALTERACAO, USUARIO_ABERTURA, USUARIO_ALTERACAO) 
                        VALUES (%s, %s, %s, GETDATE(), GETDATE(), %s, %s)
                        """,
                        [ordem_producao, produto, "Pendente", usuario_id, usuario_id],
                    )


                # Inserir registros nas tabelas KING_INSPECAO_LOTE e KING_INSPECAO_COR
                for fase in ordem_data["lotes"]:
                    fase_producao = fase["fase_producao"]
                    recurso_produtivo = fase["recurso_produtivo"]
                    total = fase["total"]

                    # Inserir na tabela KING_INSPECAO_LOTE
                    with connections["default"].cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO KING_INSPECAO_LOTE
                            (FASE_PRODUCAO, RECURSO_PRODUTIVO, TOTAL, ORDEM_PRODUCAO)
                            VALUES (%s, %s, %s, %s)
                            """,
                            [fase_producao, recurso_produtivo, total, ordem_producao],
                        )

                    # Inserir na tabela KING_INSPECAO_COR
                    for cor in fase["cores"]:
                        cor_produto = cor["cor_produto"]
                        amostra = cor["amostra"]
                        total_cor = cor["total"]

                        # Inserir na tabela KING_INSPECAO_COR
                        with connections["default"].cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO KING_INSPECAO_COR
                                (COR_PRODUTO, FASE_PRODUCAO, TOTAL, AMOSTRA, STATUS, ORDEM_PRODUCAO)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """,
                                [
                                    cor_produto,
                                    fase_producao,
                                    total_cor,
                                    amostra,
                                    "Pendente",
                                    ordem_producao,
                                ],
                            )
                
                return (True, "Inspeção criada com sucesso.", ordem_data)
        except Exception as e:
            return (False, f"Erro ao criar inspeção: {str(e)}", None)




