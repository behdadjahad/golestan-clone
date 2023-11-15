from django.urls import path

from term import views

app_name = 'user'

urlpatterns = [
    path('student/<int:pk>/courses/<int:pk>/appeal-request', views.AppealRequestStudentView.as_view(), name='appeal-request-student'),
    path('professor/<int:pk>/courses/<int:pk>/appeal-request', views.AppealRequestProfessorView.as_view(), name='appeal-request-professor'),
]