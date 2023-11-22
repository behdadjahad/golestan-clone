from django.urls import path, include
from faculty import views
from rest_framework.routers import DefaultRouter

app_name = 'faculty'

router = DefaultRouter()
router.register(r'subjects', views.ApprovedCourseViewSet, basename='approved-course')
router.register(r'faculties', views.FacultyViewSet, basename='faculty')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(router.urls)),
]
