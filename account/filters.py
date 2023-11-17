import django_filters
from account.models import Student, Professor

class StudentFilter(django_filters.FilterSet):
    major = django_filters.CharFilter(field_name='major__name', lookup_expr='icontains')
    faculty = django_filters.CharFilter(field_name='faculty__name', lookup_expr='icontains')

    class Meta:
        model = Student
        fields = ['first_name', 'last_name' ,'student_number', 'national_id', 'intrance_year', 'faculty', 'major', 'militery_service_status']
        


class ProfessorFilter(django_filters.FilterSet):
    faculty = django_filters.CharFilter(field_name='faculty__name', lookup_expr='icontains')

    class Meta:
        model = Professor
        fields = ['first_name', 'last_name' ,'professor_number', 'national_id', 'faculty', 'major', 'degree']