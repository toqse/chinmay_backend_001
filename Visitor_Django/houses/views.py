from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from .models import House, VisitHistory
from .serializers import HouseSerializer, VisitHistorySerializer
from datetime import datetime, timedelta
from django.utils import timezone
import random
from decimal import Decimal
from django.core.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

# Create your views here.

class HouseFilter(filters.FilterSet):
    ward_number = filters.NumberFilter()
    from_date = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = House
        fields = ['ward_number', 'from_date', 'to_date']

class HouseViewSet(viewsets.ModelViewSet):
    serializer_class = HouseSerializer
    filterset_class = HouseFilter
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        if self.request.user.is_staff:
            return House.objects.all()
        return House.objects.filter(panchayath=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['show_future_visits'] = False
        return context

class VisitHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = VisitHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return VisitHistory.objects.all()
        return VisitHistory.objects.filter(house__panchayath=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            visit_date = datetime.strptime(request.data['visit_date'], '%Y-%m-%d').date()
            house = House.objects.get(pk=request.data['house'])
            
            # Calculate days since start to determine the appropriate time window
            start_date = house.custom_date if house.custom_date else house.created_at.date()
            days_since_start = (visit_date - start_date).days
            
            # Determine the time window based on the period
            if days_since_start < 30:  # Weekly period
                window_days = 3  # ±3 days (total 7 days)
            elif days_since_start < 60:  # Bi-weekly period
                window_days = 7  # ±7 days (total 14 days)
            else:  # Monthly period
                window_days = 15  # ±15 days (total 30 days)
            
            # Find and delete auto-generated visits within the window
            window_start = visit_date - timedelta(days=window_days)
            window_end = visit_date + timedelta(days=window_days)
            
            VisitHistory.all_objects.filter(
                house=house,
                auto_generated=True,
                visit_date__range=(window_start, window_end)
            ).delete()
            
            return super().create(request, *args, **kwargs)
        except (ValueError, House.DoesNotExist) as e:
            raise ValidationError(str(e))

    @action(detail=False, methods=['post'])
    def check_and_generate(self, request):
        try:
            # Add validation for date range
            max_future_date = timezone.now().date() + timedelta(days=365 * 3)
            
            positive_reviews = [
                "Working properly",
                "No issues found",
                "All systems functioning well",
                "Satisfactory condition",
                "Regular maintenance confirmed",
                "No problems identified",
                "Everything in order",
                "Excellent condition",
                "Very satisfied",
                "No complaints",
            ]
            
            houses = House.objects.filter(panchayath=request.user)
            
            for house in houses:
                # Delete existing auto-generated visits
                VisitHistory.all_objects.filter(
                    house=house,
                    auto_generated=True
                ).delete()
                
                start_date = house.custom_date if house.custom_date else house.created_at.date()
                end_date = start_date + timedelta(days=365 * 3)  # 3 years from start date
                
                current_date = start_date
                
                while current_date <= end_date:
                    days_since_start = (current_date - start_date).days
                    
                    # Calculate base next date first
                    if days_since_start < 30:  # First month: Weekly
                        next_date = current_date + timedelta(days=7)
                    elif days_since_start < 60:  # Second month: Bi-weekly
                        next_date = current_date + timedelta(days=14)
                    else:  # Third month onwards: Monthly
                        next_month = current_date.replace(day=1)
                        if current_date.month == 12:
                            next_month = next_month.replace(year=current_date.year + 1, month=1)
                        else:
                            next_month = next_month.replace(month=current_date.month + 1)
                        
                        try:
                            next_date = next_month.replace(day=current_date.day)
                        except ValueError:
                            if next_month.month == 12:
                                next_date = next_month.replace(year=next_month.year + 1, month=1, day=1) - timedelta(days=1)
                            else:
                                next_date = next_month.replace(month=next_month.month + 1, day=1) - timedelta(days=1)
                    
                    # Add random variation (-4 to +4 days)
                    random_days = random.randint(-4, 4)
                    next_date += timedelta(days=random_days)
                    
                    # If lands on Sunday, move to Monday
                    if next_date.weekday() == 6:
                        next_date += timedelta(days=1)
                    
                    interval = (next_date - current_date).days
                    
                    # Skip if Sunday
                    if current_date.weekday() != 6:
                        lat_variation = Decimal(str(random.uniform(-0.00002, 0.00002)))
                        long_variation = Decimal(str(random.uniform(-0.00002, 0.00002)))
                        

                        # Add validation for coordinate variations
                        if abs(lat_variation) > Decimal('0.00002') or abs(long_variation) > Decimal('0.00002'):
                            raise ValidationError("Coordinate variation too large")
                            

                        VisitHistory.all_objects.create(
                            house=house,
                            visit_date=current_date,
                            latitude=house.latitude + lat_variation,
                            longitude=house.longitude + long_variation,
                            auto_generated=True,
                            review=random.choice(positive_reviews)
                        )
                    
                    current_date += timedelta(days=interval)
            
            return Response({'message': 'Visits have been generated successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
