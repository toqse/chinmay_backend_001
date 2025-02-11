"""
URL configuration for Visitor_Django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from houses.views import HouseViewSet, VisitHistoryViewSet
from reports.views import GenerateReportView, GenerateSixMonthReportView
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'houses', HouseViewSet, basename='house')
router.register(r'visits', VisitHistoryViewSet, basename='visit')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include(router.urls)),
    path('api/reports/', GenerateReportView.as_view(), name='generate-report'),
    path('api/reports/six-month/', GenerateSixMonthReportView.as_view(), name='generate-six-month-report'),
    path('reports/', include('reports.urls')),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
