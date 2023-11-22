from django.urls import path, include
from term import views
from rest_framework.routers import DefaultRouter

app_name = 'term'

router1 = DefaultRouter()
router1.register(r'courses', views.TermCourseViewSet, basename='term-course')
router2 = DefaultRouter()
router2.register(r'studying-evidence', views.EnrollmentCertificateRequestVeiwSet, basename='studying-evidence')

urlpatterns = [
    path('', include(router1.urls)),
    path('student/<int:pk>/course-selection/create/', views.CourseSelectionCreationFormAPIView.as_view(), name='course-selection-create'),
    path('student/<int:pk>/course-selection/', views.CourseSelectionListAPIView.as_view(), name='course-selection-list'),
    path('student/<int:pk>/course-selection/check/', views.CourseSelectionCheckAPIView.as_view(), name='course-selection-check'),
    path('student/<int:pk>/course-selection/submit/', views.CourseSelectionSubmitAPIView.as_view(), name='course-selection-submit'),
    path('student/<int:pk>/course-selection/send/', views.CourseSelectionSendAPIView.as_view(), name='course-selection-send'),
    path('professor/<int:pk>/students-selection-forms/', views.CourseSelectionStudentFormsAPIView.as_view(), name='students-selection-forms'),
    path('professor/<int:pk>/students-selection-forms/<int:s_pk>/', views.CourseSelectionStudentFormsDetailAPIView.as_view(), name='student-selection-form'),
    
    path('student/<int:s_pk>/', include(router2.urls)),
    path('assistant/<int:pk>/studying-evidence/', views.EnrollmentCertificateRequestsAPIView.as_view(), name='studying-evidences'),
    path('assistant/<int:a_pk>/studying-evidence/<int:pk>/', views.EnrollmentCertificateRequestsDetailAPIView.as_view(), name='studying-evidences-detail'),
]   