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
