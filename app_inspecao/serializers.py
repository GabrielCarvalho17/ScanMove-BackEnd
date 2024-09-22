from rest_framework import serializers


class BaseSerializer(serializers.Serializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation


class DefeitoLancadoSerializer(BaseSerializer):
    quantidade = serializers.IntegerField(required=True)
    observacao = serializers.CharField(required=False, allow_null=True)
    codigo_defeito = serializers.CharField(max_length=10)
    descricao_defeito = serializers.CharField(max_length=100)
    tipo_defeito = serializers.CharField(max_length=10)
    lancado_por = serializers.CharField(max_length=25)
    alterado_por = serializers.CharField(max_length=25)
    data_lancado = serializers.DateTimeField()
    data_alterado = serializers.DateTimeField()
    url_imagens = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )


class CorProdutoSerializer(BaseSerializer):
    cor_produto = serializers.CharField(max_length=10)
    desc_cor_produto = serializers.CharField(max_length=40)
    qtde_s = serializers.IntegerField(required=True)
    amostra = serializers.IntegerField(
        required=False, allow_null=True
    )  # Permitindo sobrescrever
    status = serializers.CharField(default="Pendente")

    # Método para calcular a amostra com base no valor de qtde_s
    def get_amostra(self, qtde_s):
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
            if criterio["min"] <= qtde_s <= criterio["max"]:
                return criterio["amostra"]

        return qtde_s  # Se não se encaixar em nenhum critério, retorna o próprio qtde_s

    # Sobrescrevendo o to_representation para garantir que amostra esteja presente
    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Se o valor de 'amostra' estiver vazio ou None, calcular o valor
        if not data.get("amostra"):
            data["amostra"] = self.get_amostra(data["qtde_s"])

        return data


class FaseProducaoSerializer(BaseSerializer):
    fase_producao = serializers.CharField(max_length=5, required=True)
    desc_fase_producao = serializers.CharField(
        max_length=40, required=False, allow_null=True
    )
    qtde_em_processo = serializers.IntegerField(required=True)


class OrdemProducaoSerializer(BaseSerializer):
    ordem_producao = serializers.CharField(max_length=8, required=True)
    fases = FaseProducaoSerializer(many=True)


class OrdemInspecaoSerializer(BaseSerializer):
    ordem_producao = serializers.CharField(max_length=8, required=True)
    ordem_inspecao = serializers.IntegerField()
    produto = serializers.CharField(max_length=12)
    status = serializers.CharField(max_length=9)
    data_abertura = serializers.DateTimeField()
    data_encerramento = serializers.DateTimeField(allow_null=True)  
    usuario_abertura = serializers.CharField(max_length=25) 
    usuario_alteracao = serializers.CharField(max_length=25, allow_null=True) 
    fases = FaseProducaoSerializer(many=True)

