from django.urls import path, include
from account import views
from rest_framework.routers import DefaultRouter

app_name = 'account'

router1 = DefaultRouter()
router1.register(r'students', views.StudentViewSet, basename='students')
router2 = DefaultRouter()
router2.register(r'professors', views.ProfessorViewSet, basename='professors')

urlpatterns = [
    path('', include(router1.urls)),
    path('', include(router2.urls)),
    path('students/<int:pk>/class-schedule/', views.StudentClassScheduleView.as_view(), name='class-schedule'),
    path('students/<int:pk>/exam-schedule/', views.StudentExamScheduleView.as_view(), name='exam-schedule'),
]