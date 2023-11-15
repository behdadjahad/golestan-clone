from django.urls import path, include
from term import views
from rest_framework.routers import DefaultRouter

app_name = 'term'

router = DefaultRouter()
router.register(r'courses', views.TermCourseViewSet, basename='term-course')

urlpatterns = [
    path('', include(router.urls))
]