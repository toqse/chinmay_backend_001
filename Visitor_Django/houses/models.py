from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta
import random
from accounts.models import User
from decimal import Decimal
from django.utils import timezone

class House(models.Model):
    panchayath = models.ForeignKey(User, on_delete=models.CASCADE)
    house_number = models.CharField(max_length=50)
    ward_number = models.IntegerField(null=True, blank=True)
    resident_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='house_photos/', null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    custom_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['panchayath', 'house_number']

class VisitHistoryManager(models.Manager):
    def get_queryset(self):
        # By default, only return visits up to current date
        return super().get_queryset().filter(visit_date__lte=timezone.now().date())
    
    def past_visits(self):
        return self.get_queryset()
    
    def future_visits(self):
        return super().get_queryset().filter(visit_date__gt=timezone.now().date())

class VisitHistory(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    visited = models.BooleanField(default=False)
    auto_generated = models.BooleanField(default=False)
    review = models.TextField(null=True, blank=True)
    superseded = models.BooleanField(default=False)
    
    objects = VisitHistoryManager()
    all_objects = models.Manager()
    
    class Meta:
        ordering = ['visit_date']

@receiver(post_save, sender=House)
def create_visit_history(sender, instance, created, **kwargs):
    if created and instance.custom_date:
        current_date = instance.custom_date
        end_date = current_date + timedelta(days=365 * 3)  # 3 years from custom_date
        
        # Generate visit history starting from custom_date
        generate_visit_history(instance, current_date, end_date)

def generate_visit_history(house, start_date, end_date):
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
        
        # Skip if current date is Sunday
        if current_date.weekday() != 6:
            lat_variation = Decimal(str(random.uniform(-0.00002, 0.00002)))
            long_variation = Decimal(str(random.uniform(-0.00002, 0.00002)))
            

            VisitHistory.all_objects.create(
                house=house,
                visit_date=current_date,
                latitude=house.latitude + lat_variation,
                longitude=house.longitude + long_variation,
                auto_generated=True,
                review=random.choice(positive_reviews)
            )
        
        current_date += timedelta(days=interval)



