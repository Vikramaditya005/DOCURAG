from rest_framework import serializers
from .models import Document, QueryLog

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class QueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryLog
        fields = '__all__'
