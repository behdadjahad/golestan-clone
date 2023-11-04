from django.urls import path, include

from user import views

app_name = 'user'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'), 
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('reset_password/<str:token>/', ResetPasswordView.as_view(), name='reset_password'),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),
    
]