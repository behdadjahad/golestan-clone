from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularJSONAPIView,SpectacularSwaggerView

urlpatterns = [
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/', SpectacularJSONAPIView.as_view(), name='schema'),
    path('admin/', admin.site.urls),
    path('api/v1/users/', include('user.urls')),
    path('api/v1/users/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('api/v1/faculty/', include('faculty.urls')),
    path('api/v1/term/', include('term.urls')),
    path('api/v1/account/', include('account.urls')),
]
