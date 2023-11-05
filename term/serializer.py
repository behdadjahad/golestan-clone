from rest_framework import serializers

from term.models import TermCourse
from faculty.models import ApprovedCourse


class TermSerializer(serializers.ModelSerializer):
    units = ApprovedCourse.objects.get(name='TermCourse.name', units='units')
    available_capacity = ''# should initiate with course capacity - students who take it

    class Meta:
        model = TermCourse
        fields = ['name', 'units', 'class_days_and_times', 'course_professor', 'exam_time', 'available_capacity']
