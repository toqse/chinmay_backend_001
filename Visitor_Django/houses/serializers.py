from rest_framework import serializers
from .models import House, VisitHistory
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

class VisitHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitHistory
        fields = '__all__'
        read_only_fields = ('auto_generated',)

class HouseSerializer(serializers.ModelSerializer):
    visits = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = '__all__'
        read_only_fields = ('panchayath',)

    def get_visits(self, obj):
        # Use the default manager which only returns past visits
        visits = obj.visits.all()
        return VisitHistorySerializer(visits, many=True).data

    def compress_image(self, image):
        if not image:
            return image
            
        # Open the uploaded image
        img = Image.open(image)
        
        # Convert to RGB if image is in RGBA mode
        if img.mode == 'RGBA':
            img = img.convert('RGB')
            
        # Set maximum dimension while maintaining aspect ratio
        max_size = (800, 800)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Create a BytesIO object to store the compressed image
        output = BytesIO()
        
        # Save the image with reduced quality
        img.save(output, format='JPEG', quality=70, optimize=True)
        output.seek(0)
        
        # Create a new InMemoryUploadedFile with the compressed image
        return InMemoryUploadedFile(
            output,
            'ImageField',
            f"{image.name.split('.')[0]}.jpg",
            'image/jpeg',
            sys.getsizeof(output),
            None
        )

    def create(self, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = self.compress_image(validated_data['photo'])
        validated_data['panchayath'] = self.context['request'].user
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        if 'photo' in validated_data:
            validated_data['photo'] = self.compress_image(validated_data['photo'])
        return super().update(instance, validated_data) 