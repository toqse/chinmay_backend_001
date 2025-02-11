from django.urls import path
from .views import GenerateReportView, GenerateSixMonthReportView

urlpatterns = [
    path('generate/', GenerateReportView.as_view(), name='generate-report'),
    path('generate-six-month/', GenerateSixMonthReportView.as_view(), name='generate-six-month-report'),
] 