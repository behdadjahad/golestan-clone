from django.urls import path, include
from term import views
from rest_framework.routers import DefaultRouter

app_name = 'term'

router = DefaultRouter()
router.register(r'courses', views.TermCourseViewSet, basename='term-course')

urlpatterns = [
    path('', include(router.urls)),
    path('student/<int:pk>/course-selection/create/', views.CourseSelectionCreationFormAPIView.as_view(), name='course-selection-create'),
    path('student/<int:pk>/course-selection/', views.CourseSelectionListAPIView.as_view(), name='course-selection-list'),
    path('student/<int:pk>/course-selection/check/', views.CourseSelectionCheckAPIView.as_view(), name='course-selection-check'),
]