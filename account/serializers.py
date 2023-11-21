from rest_framework import serializers
from account.models import Student, Professor
from term.models import Term, TermCourse
from faculty.models import Faculty


class StudentSerializer(serializers.ModelSerializer) :
    faculty_name = serializers.StringRelatedField(source='faculty.name', read_only=True)
    major_name = serializers.StringRelatedField(source='major.name', read_only=True)
    supervisor_name = serializers.StringRelatedField(source='supervisor.full_name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'pk',
            'first_name',
            'last_name',
            'student_number',
            'intrance_year',
            'faculty_name',
            'major_name',
            'supervisor_name',
            'militery_service_status',
            'courses',
            'years',            
        ]
        read_only_fields = [
            'pk',
            'student_number',
            'intrance_year',
            'faculty',
            'major',
            'supervisor',
            'courses',
            'years',
            'militery_service_status',
        ]
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['courses'] = [course.name for course in instance.courses.all()]
        return representation
    
        
        
class ProfessorSerializer(serializers.ModelSerializer) :
    faculty_name = serializers.StringRelatedField(source='faculty.name', read_only=True)
    
    class Meta:
        model = Professor
        fields = [
            'pk',
            'first_name',
            'last_name',
            'professor_number',
            'faculty_name',
            'presented_courses',
            'major',
            'expertise',
            'degree',
        ]
        read_only_fields = [
            'pk',
            'professor_number',
            'presented_courses',
            'faculty',
            'major',
            'expertise',
        ]
        
    def to_representation(self, instance):
            representation = super().to_representation(instance)
            representation['presented_courses'] = [course.name for course in instance.presented_courses.all()]
            return representation
        
        
class StudentClassScheduleSerializer(serializers.ModelSerializer) :
    course_name = serializers.StringRelatedField(source='name.course_name', read_only=True)
    class Meta:
        model = TermCourse
        fields = [
            'course_name',
            'class_days_and_times'
        ]
     
  
class StudentExamScheduleSerializer(serializers.ModelSerializer) :
    course_name = serializers.StringRelatedField(source='name.course_name', read_only=True)
    class Meta:
        model = TermCourse
        fields = [
            'course_name',
            'exam_time',
        ]

class InputFacultiesSerialiser(serializers.Serializer):
    name = serializers.CharField(max_length=100)


class OutputFacultiesSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = "__all__"

class OutputFacultySerialiser(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ("name",)