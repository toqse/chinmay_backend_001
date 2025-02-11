from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer
from django.contrib.auth import authenticate
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import serializers

# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"error": "Only admin users can create new users"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(request=request, email=email, password=password)
        
        if not user:
            user_exists = User.objects.filter(email=email).exists()
            if user_exists:
                msg = 'Password is incorrect.'
            else:
                msg = 'Email not found.'
            raise serializers.ValidationError(msg)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_panchayath': user.is_panchayath,
            'ward_count': user.ward_count,
            'product_number': user.product_number,
            'product_name': user.product_name,
        })

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Delete the user's token to logout
        request.user.auth_token.delete()
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        user_id = request.data.get('user_id')
        new_password = request.data.get('new_password')

        if not user_id or not new_password:
            return Response(
                {"error": "Both user_id and new_password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id, is_panchayath=True)
        except User.DoesNotExist:
            return Response(
                {"error": "Panchayath user not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Set new password
        user.set_password(new_password)
        user.plain_password = new_password  # Update plain_password field
        user.save()

        # Invalidate existing token if any
        Token.objects.filter(user=user).delete()

        return Response({
            "message": f"Password updated successfully for user {user.email}"
        }, status=status.HTTP_200_OK)
