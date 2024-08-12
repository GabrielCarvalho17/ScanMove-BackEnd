from rest_framework import serializers

class MateriaisSerializer(serializers.Serializer):
    peca = serializers.CharField(max_length=6)
    partida = serializers.CharField(max_length=6)
    material = serializers.CharField(max_length=11)
    filial = serializers.CharField(max_length=25)
    cor_material = serializers.CharField(max_length=10)
    unid_estoque = serializers.CharField(max_length=5)
    qtde = serializers.DecimalField(max_digits=10, decimal_places=3)
    desc_cor_material = serializers.CharField(max_length=50)
    localizacao = serializers.CharField(max_length=8)
    desc_material = serializers.CharField(max_length=80)  

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation

class LocalizacoesSerializer(serializers.Serializer):
    localizacao = serializers.CharField(max_length=8)
    filial = serializers.CharField(max_length=25)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation

class MovimentacaoItemSerializer(serializers.Serializer):
    peca = serializers.CharField(max_length=6)
    partida = serializers.CharField(max_length=6)
    material = serializers.CharField(max_length=11)
    desc_material = serializers.CharField(max_length=80)
    cor_material = serializers.CharField(max_length=10)
    desc_cor_material = serializers.CharField(max_length=50)
    unidade = serializers.CharField(max_length=5)
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=3)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation

from rest_framework import serializers

class MovimentacaoItemSerializer(serializers.Serializer):
    peca = serializers.CharField(max_length=6)
    partida = serializers.CharField(max_length=6)
    material = serializers.CharField(max_length=11)
    desc_material = serializers.CharField(max_length=80)
    cor_material = serializers.CharField(max_length=10)
    desc_cor_material = serializers.CharField(max_length=50)
    unidade = serializers.CharField(max_length=5)
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=3)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation

class MovimentacaoSerializer(serializers.Serializer):
    movimentacao = serializers.IntegerField(read_only=True)  # Tornar read_only para criação
    data_inicio = serializers.DateTimeField()
    data_modificacao = serializers.DateTimeField()
    status = serializers.CharField(max_length=10)
    usuario = serializers.CharField(max_length=25)
    origem = serializers.CharField(max_length=8)
    destino = serializers.CharField(max_length=8)
    total_pecas = serializers.IntegerField()
    filial_origem = serializers.CharField(max_length=25, read_only=True)  # Apenas leitura
    filial_destino = serializers.CharField(max_length=25, read_only=True)  # Apenas leitura
    itens = MovimentacaoItemSerializer(many=True)

    def validate(self, data):
        if data['status'] != 'ANDAMENTO' and not data.get('filial_destino'):
            raise serializers.ValidationError(
                "O campo 'filial_destino' não pode ficar em branco, exceto quando o status for 'ANDAMENTO'."
            )
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in representation:
            if isinstance(representation[field], str):
                representation[field] = representation[field].strip()
        return representation


