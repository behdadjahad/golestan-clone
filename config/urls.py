from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('user.urls')),
    path('api/v1/users/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('ap1/v1/terms/', include('term.urls'))
    
]
