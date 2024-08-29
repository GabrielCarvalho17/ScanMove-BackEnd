from rest_framework import serializers


class LocalizacoesSerializer(serializers.Serializer):
    localizacao = serializers.CharField(max_length=8)
    filial = serializers.CharField(max_length=25)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation


class PecaSerializer(serializers.Serializer):
    peca = serializers.CharField(max_length=6)
    partida = serializers.CharField(
        max_length=6, required=False, allow_null=True, allow_blank=True
    )
    material = serializers.CharField(max_length=11)
    desc_material = serializers.CharField(max_length=80)
    cor_material = serializers.CharField(max_length=10)
    desc_cor_material = serializers.CharField(max_length=50)
    unidade = serializers.CharField(max_length=5)
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=3)
    filial = serializers.CharField(max_length=25)
    localizacao = serializers.CharField(
        max_length=8, required=False, allow_null=True, allow_blank=True
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation


class MovimentacaoSerializer(serializers.Serializer):
    movimentacao = serializers.IntegerField(
        read_only=True
    )  # Tornar read_only para criação
    data_inicio = serializers.DateTimeField()
    data_modificacao = serializers.DateTimeField()
    status = serializers.CharField(max_length=10)
    usuario = serializers.CharField(max_length=25)
    origem = serializers.CharField(max_length=8)
    destino = serializers.CharField(max_length=8)
    total_pecas = serializers.IntegerField()
    filial_origem = serializers.CharField(
        max_length=25, read_only=True
    )  # Apenas leitura
    filial_destino = serializers.CharField(
        max_length=25, read_only=True
    )  # Apenas leitura
    pecas = PecaSerializer(many=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation


class IncluiPecasSerializer(serializers.Serializer):
    data_modificacao = serializers.DateTimeField()
    pecas = PecaSerializer(many=True)


class AtualizarMovimentacaoSerializer(serializers.Serializer):
    origem = serializers.CharField(
        required=False,
        max_length=8,
        help_text="Código da origem da movimentação. Deve ser diferente do destino.",
    )
    destino = serializers.CharField(
        required=False,
        max_length=8,
        help_text="Código do destino da movimentação. Deve ser diferente da origem.",
    )
    status = serializers.BooleanField(
        required=False,
        help_text="Indica se a movimentação deve ser finalizada. Defina como True para finalizar.",
    )
    data_modificacao = serializers.DateTimeField(
        required=True,
        help_text="Data e hora da última modificação na movimentação. Este campo é obrigatório.",
    )
