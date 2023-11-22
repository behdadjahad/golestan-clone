import django_filters
from term.models import TermCourse

class TermCourseFilter(django_filters.FilterSet):
    course_name = django_filters.CharFilter(field_name='name__course_name', lookup_expr='icontains')
    faculty = django_filters.CharFilter(field_name='name__faculty__name', lookup_expr='icontains')
    term = django_filters.NumberFilter(field_name='term__id')

    class Meta:
        model = TermCourse
        fields = ['course_name', 'faculty', 'term']