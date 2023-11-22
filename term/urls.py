from django.urls import path, include
from term import views
from rest_framework.routers import DefaultRouter
from term.views import (
    TermsListView, TermsDetailView,
    StudentApprovedCourseView, StudentPassedCourseView, StudentTermCourseView,
    StudentRemainedTermView, EmergencyRemoveRequestView, CourseRemovalListView,
    CourseRemovalDetailView, TermRemoveRequestView, TermRemovalListView,
    TermRemovalDetailView)

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

    path('student/<int:std_id>/course/<int:co_id>/reconsideration/', views.ReconsiderationRequestStudentView.as_view(), name="student-reconsideration"),
    path('professor/<int:std_id>/course/<int:co_id>/reconsideration/', views.ReconsiderationRequestProfessorView.as_view(), name="student-reconsideration"),

    
    path('student/<int:pk>/course-substitution/create/', views.CourseSubstitutionCreationFormAPIView.as_view(), name='course-substitution-create'),
    path('student/<int:pk>/course-substitution/', views.CourseSubstitutionListAPIView.as_view(), name='course-substitution-list'),
    path('student/<int:pk>/course-substitution/check/', views.CourseSubstitutionCheckAPIView.as_view(), name='course-substitution-check'),
    path('student/<int:pk>/course-substitution/submit/', views.CourseSubstitutionSubmitAPIView.as_view(), name='course-substitution-submit'),
    path('student/<int:pk>/course-substitution/send/', views.CourseSubstitutionSendAPIView.as_view(), name='course-substitution-send'),
    path('professor/<int:pk>/students-substitution-forms/', views.CourseSubstitutionStudentFormsAPIView.as_view(), name='students-substitution-forms'),
    path('professor/<int:pk>/students-substitution-forms/<int:s_pk>/', views.CourseSubstitutionStudentFormsDetailAPIView.as_view(), name='student-substitution-form'),
<<<<<<< HEAD
    
    path('student/<int:s_pk>/', include(router2.urls)),
    path('assistant/<int:pk>/studying-evidence/', views.EnrollmentCertificateRequestsAPIView.as_view(), name='studying-evidences'),
    path('assistant/<int:a_pk>/studying-evidence/<int:pk>/', views.EnrollmentCertificateRequestsDetailAPIView.as_view(), name='studying-evidences-detail'),
=======
#  ----------------------------------------------------------------
    path('term/', TermsListView.as_view(), name='term-list'),
    path('term/<int:pk>', TermsDetailView.as_view(),
        name='term-detail'),
    path('student/<int:pk>/my_courses', StudentApprovedCourseView.as_view(),
        name='student-approvedcourses'),
    path('student/<int:pk>/passed_courses_report',
        StudentPassedCourseView.as_view(), name='student-passed-courses'),
    path('student/<int:pk>/term_courses',
        StudentTermCourseView.as_view(), name='student-term-courses'),
    path('student/<int:pk>/remaining_terms',
        StudentRemainedTermView.as_view(), name='student-remained-term'),
    path('student/<int:s_pk>/emergency_remove/<int:c_pk>',
        EmergencyRemoveRequestView.as_view(),
        name='emergency-remove-request'),
    path('assistant/<int:pk>/emergency_remove',
        CourseRemovalListView.as_view(),
        name='emergency-remove-list'),
    path('assistant/<int:s_pk>/emergency_remove/<int:c_pk>',
        CourseRemovalDetailView.as_view(),
        name='emergency-remove-detail'),

    path('student/<int:a_pk>/term_remove/<int:e_pk>',
        TermRemoveRequestView.as_view(),
        name='term-remove-request'),
    path('assistant/<int:pk>/term',
        TermRemovalListView.as_view(),
        name='term-remove-list'),
    path('assistant/<int:a_pk>/term_remove/<int:e_pk>',
        TermRemovalDetailView.as_view(),
        name='term-remove-detail'),
   
>>>>>>> origin/feature/endpoint-e-i-j
]   