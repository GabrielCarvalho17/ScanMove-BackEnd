from rest_framework import serializers


class DefeitoLancadoSerializer(serializers.Serializer):
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


class CorProdutoSerializer(serializers.Serializer):
    cor_produto = serializers.CharField(max_length=10)
    desc_cor_produto = serializers.CharField(max_length=40)
    total = serializers.IntegerField(required=True)
    amostra = serializers.IntegerField(required=False)
    status = serializers.CharField(default="Pendente")
    defeitos = DefeitoLancadoSerializer(many=True, required=False)


class LoteProducaoSerializer(serializers.Serializer):
    recurso_produtivo = serializers.CharField(max_length=5)
    fase_producao = serializers.CharField(max_length=5)
    desc_recurso = serializers.CharField(max_length=40)
    desc_fase_producao = serializers.CharField(max_length=40)
    total = serializers.IntegerField(required=True)
    cores = CorProdutoSerializer(many=True)


class OrdemInspecaoSerializer(serializers.Serializer):
    ordem_producao = serializers.CharField(max_length=8, required=True)
    produto = serializers.CharField(max_length=12)
    status = serializers.CharField(max_length=9, required=False)
    data_abertura = serializers.DateTimeField(required=False)
    data_alteracao = serializers.DateTimeField(required=False)
    usuario_abertura = serializers.CharField(
        max_length=25,
        required=False,
    )
    usuario_alteracao = serializers.CharField(
        max_length=25,
        required=False,
    )
    lotes = LoteProducaoSerializer(many=True)


