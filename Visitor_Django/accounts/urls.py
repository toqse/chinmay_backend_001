from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomAuthToken, LogoutView, ChangePasswordView

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name='auth_token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
] + router.urls 