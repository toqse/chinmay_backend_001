from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_staff = serializers.BooleanField(default=False)
    is_superuser = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_panchayath', 
                 'ward_count', 'phone_number', 'is_staff', 'is_superuser', 'plain_password', 'product_number', 'product_name')

    def create(self, validated_data):
        password = validated_data['password']
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            is_panchayath=validated_data.get('is_panchayath', False),
            ward_count=validated_data.get('ward_count', 0),
            phone_number=validated_data.get('phone_number', ''),
            is_staff=validated_data.get('is_staff', False),
            is_superuser=validated_data.get('is_superuser', False),
            product_number=validated_data.get('product_number', ''),
            product_name=validated_data.get('product_name', '')
        )
        user.plain_password = password
        user.save()
        return user 