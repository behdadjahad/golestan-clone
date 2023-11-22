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
    path('admin/professors/', views.ProfessorApi.as_view(), name='professors'),
    path('admin/students/', views.StudentApi.as_view(), name='students'),
    path('admin/assistants/', views.AssistantApi.as_view(), name='assistants'),
    path('admin/faculties/', views.FacultyApi.as_view(), name='faculties'),
    path('admin/term/', views.TermsApi.as_view(), name='terms'),
    path('admin/professor/<int:pk>/', views.ProfessorDetailApi.as_view(), name='professor-detail'),
    path('admin/student/<int:pk>/', views.StudentDetailApi.as_view(), name='student-detail'),
    path('admin/assistant/<int:pk>/', views.AsistantDetailApi.as_view(), name='assistant-detail'),
    path('admin/faculty/<int:pk>/', views.FacultyDetailApi.as_view(), name='faculty-detail'),
    path('admin/term/<int:pk>/', views.TermDetailApi.as_view(), name='term-detail'),

]