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


        path('term/', views.TermsListView.as_view(), name='term-list'),
    path('term/<int:pk>', views.TermsDetailView.as_view(),
        name='term-detail'),
    path('student/<int:pk>/my_courses', views.StudentApprovedCourseView.as_view(),
        name='student-approvedcourses'),
    path('student/<int:pk>/passed_courses_report',
        views.StudentPassedCourseView.as_view(), name='student-passed-courses'),
    path('student/<int:pk>/term_courses',
        views.StudentTermCourseView.as_view(), name='student-term-courses'),
    path('student/<int:pk>/remaining_terms',
        views.StudentRemainedTermView.as_view(), name='student-remained-term'),
    path('student/<int:s_pk>/emergency_remove/<int:c_pk>',
        views.EmergencyRemoveRequestView.as_view(),
        name='emergency-remove-request'),
    path('assistant/<int:pk>/emergency_remove',
        views.CourseRemovalListView.as_view(),
        name='emergency-remove-list'),
    path('assistant/<int:s_pk>/emergency_remove/<int:c_pk>',
        views.CourseRemovalDetailView.as_view(),
        name='emergency-remove-detail'),

    path('student/<int:a_pk>/term_remove/<int:e_pk>',
        views.TermRemoveRequestView.as_view(),
        name='term-remove-request'),
    path('assistant/<int:pk>/term',
        views.TermRemovalListView.as_view(),
        name='term-remove-list'),
    path('assistant/<int:a_pk>/term_remove/<int:e_pk>',
        views.TermRemovalDetailView.as_view(),
        name='term-remove-detail'),
   
]   