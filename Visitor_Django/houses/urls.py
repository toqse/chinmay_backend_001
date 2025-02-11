from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import HouseViewSet, VisitHistoryViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register('houses', HouseViewSet, basename='house')
router.register('visits', VisitHistoryViewSet, basename='visit')

urlpatterns = router.urls 
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)