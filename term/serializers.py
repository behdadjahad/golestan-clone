from rest_framework import serializers
from term.models import TermCourse, Term, RegistrationRequest, ReconsiderationRequest
from account.models import Student
from datetime import datetime, date

class TermCourseSerializer(serializers.ModelSerializer) :
    # course_name = serializers.StringRelatedField(source='name.course_name', read_only=True)
    # term_name = serializers.StringRelatedField(source='term.term_name', read_only=True)
    # course_professor_name = serializers.StringRelatedField(source='course_professor', read_only=True)

    class Meta :
        model = TermCourse
        fields = [
            "id",
            "name",
            "class_days_and_times",
            "exam_time",
            "exam_place",
            "course_professor",
        "course_capacity",
            "term",
        ]
        
    def validate(self, attrs) :
        term = attrs["term"]
        repairing_unit_selection_end_time = term.repairing_unit_selection_end_time    
        term_end_time = term.term_end_time
        now = datetime.now()
        now = date(now.year, now.month, now.day)
        repairing_unit_selection_end_time = date(repairing_unit_selection_end_time.year, repairing_unit_selection_end_time.month, repairing_unit_selection_end_time.day)
        term_end_time = date(term_end_time.year, term_end_time.month, term_end_time.day)
        if now < term_end_time and now > repairing_unit_selection_end_time:
            raise serializers.ValidationError("Cannot create TermCourse instance. Invalid datetime range.")
        
        course = attrs["name"]
        if course.course_type == "practical" and (attrs.get("exam_time", None) is not None or attrs.get("exam_place", None) is not None):
            raise serializers.ValidationError("Cannot create TermCourse instance. practical courses cannot have exam_time and exam_place.")
        
        
        
        return attrs
    
    
class CourseSelectionSerializer(serializers.ModelSerializer) :
    class Meta :
        model = RegistrationRequest
        fields = [
            "term",
            "student",
            "courses",
            "confirmation_status",
        ]

    def validate(self, attrs):
        term = attrs['term']
        start = term.unit_selection_start_time
        end = term.unit_selection_end_time
        now = datetime.now()
        now = datetime(now.year, now.month, now.day, now.hour, now.minute)
        start = datetime(start.year, start.month, start.day, start.hour, start.minute)
        end = datetime(end.year, end.month, end.day, end.hour, end.minute)
        if not (now < end and now > start):
            raise serializers.ValidationError("You are ubable to access course selection. Invalid datetime range.")
        return attrs

    
class CourseSelectionCheckSerializer(serializers.Serializer) :
    OPTION_CHOICES = (
        ('add', 'Add'),
        ('delete', 'Delete'),
    )
    course = serializers.PrimaryKeyRelatedField(many=True, queryset=TermCourse.objects.all())
    option = serializers.ChoiceField(choices=OPTION_CHOICES)
    
    def validate(self, attrs) :
        student = Student.objects.get(pk=self.context['pk'])
        course = attrs['course'][0]
        
        if attrs['option'] == 'add' :
            # 1st validation
            precourses = course.name.pre_requisites.all()
            for course in precourses :
                termcourse = course.termcourse_set.filter(term=Term.objects.all().last()).first()
                ispassed = termcourse.coursestudent_set.filter(student=student, course_status='passed').exists()
                if not ispassed :
                    raise serializers.ValidationError(f"You haven't passed { course } course.")
                
            # 2nd validation
            repeated = course in RegistrationRequest.objects.filter(term=Term.objects.all().last(), student=student).first().courses.all()
            passed = course.coursestudent_set.filter(student=student, course_status='passed').exists()
            if repeated or passed :
                raise serializers.ValidationError(f"You have already registered { course } course.") 
            
            # 8th validation
            stu_faculty = student.faculty # it can be editted !!!!
            course_faculty = course.name.faculty
            if stu_faculty != course_faculty :
                raise serializers.ValidationError(f"Course { course } is not offered by your faculty.")
        
        elif attrs['option'] == 'delete' :
            # 4th validation
            registered_courses = RegistrationRequest.objects.filter(term=Term.objects.all().last(), student=student).first().courses.all()
            for course_ in  registered_courses:
                if course.name in course_.name.co_requisites.all() :
                    raise serializers.ValidationError(f"The { course } course is the co-requisites of {course_} course")
            
        return attrs
            

class CourseSelectionStudentFormsSerializers(serializers.ModelSerializer) :
    class Meta :
        model = RegistrationRequest
        fields = [
            "confirmation_status",
            "term",
            "student",
            "courses",   
        ]

class InputReconsiderationStudentSerializer(serializers.Serializer):
    reconsideration_text = serializers.CharField(max_length=1024)


class OutputReconsiderationStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconsiderationRequest
        fields = "__all__"



class InputReconsiderationProfessorSerializer(serializers.Serializer):
    reconsideration_response = serializers.CharField(max_length=1024)


class OutputReconsiderationProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconsiderationRequest
        fields = "__all__"