from rest_framework import serializers
from .models import Place_info, Place_keywords, Plan


class Place_infoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Place_info
        fields = ("__all__")
class Place_keywordsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Place_keywords
        fields = ("__all__")

class Plan_Serializer(serializers.ModelSerializer):

    class Meta:
        model = Plan
        fields = ("__all__")



