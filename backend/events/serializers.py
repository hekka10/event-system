from rest_framework import serializers
from .models import Event, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    organizer_email = serializers.ReadOnlyField(source='organizer.email')

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'date', 'location', 
            'category', 'category_name', 'price', 'capacity', 
            'image', 'organizer', 'organizer_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['organizer', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Automatically set the organizer to the current user
        validated_data['organizer'] = self.context['request'].user
        return super().create(validated_data)
