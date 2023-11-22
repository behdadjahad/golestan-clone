from rest_framework import serializers
from account.models import Student, Professor, EducationalAssistant
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

    
class UpdateFacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = "__all__"

class InputProfessorsSerialiser(serializers.Serializer):
    password = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=9)
    phone_number = serializers.CharField(max_length=11)
    national_id = serializers.CharField(max_length=10)
    birth_date = serializers.DateField()
    gender = serializers.CharField(max_length=1)
    faculty = serializers.IntegerField()
    major = serializers.IntegerField()
    expertise = serializers.CharField(max_length=100)
    degree = serializers.CharField(max_length=100)


class OutputProfessorsSerialiser(serializers.ModelSerializer):
        
    class Meta:
        model = Professor
        # fields = ("first_name", "last_name", "email", "account_number", "national_id", "gender", "created_at", "updated_at")
        fields = "__all__"


class UpdateProfessorSerialiser(serializers.ModelSerializer):
        
    class Meta:
        model = Professor
        fields = ("first_name", "last_name", "email", "professor_number", "national_id", "gender")
        # fields = "__all__"


class InputStudentsSerialiser(serializers.Serializer):
    password = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=9)
    phone_number = serializers.CharField(max_length=11)
    national_id = serializers.CharField(max_length=10)
    birth_date = serializers.DateField()
    gender = serializers.CharField(max_length=1)
    entrance_year = serializers.DateField()
    entrance_term = serializers.CharField(max_length=225)
    military_service_status = serializers.CharField(max_length=20)
    faculty = serializers.IntegerField()
    major = serializers.IntegerField()


class OutputStudentsSerialiser(serializers.ModelSerializer):
        
    class Meta:
        model = Student
        # fields = ("first_name", "last_name", "email", "account_number", "national_id", "gender", "created_at", "updated_at")
        fields = "__all__"


class UpdateStudentSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = Student
        fields = ("first_name", "last_name", "email", "student_number", "national_id", "gender")
        # fields = "__all__"


class InputAssistantsSerialiser(serializers.Serializer):
    password = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=9)
    phone_number = serializers.CharField(max_length=11)
    national_id = serializers.CharField(max_length=10)
    birth_date = serializers.DateField()
    gender = serializers.CharField(max_length=1)
    faculty = serializers.IntegerField()


class OutputAsistantsSerialiser(serializers.ModelSerializer):
        
    class Meta:
        model = EducationalAssistant
        # fields = ("first_name", "last_name", "email", "account_number", "national_id", "gender", "created_at", "updated_at")
        fields = "__all__"


class UpdateAssistantSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = EducationalAssistant
        fields = ("first_name", "last_name", "email", "educational_assistant_number", "national_id", "gender")
        # fields = "__all__"
        


class InputTermsSerialiser(serializers.Serializer):

    term_name = serializers.CharField(max_length=100)
    unit_selection_start_time = serializers.DateTimeField()
    unit_selection_end_time = serializers.DateTimeField()
    courses_start_time = serializers.DateField()
    courses_end_time = serializers.DateField()
    repairing_unit_selection_start_time = serializers.DateTimeField()
    repairing_unit_selection_end_time = serializers.DateTimeField()
    emergency_deletion_start_time = serializers.DateTimeField()
    emergency_deletion_end_time = serializers.DateTimeField()
    exams_start_time = serializers.DateField()
    term_end_time = serializers.DateField()


class OutputTermsSerialiser(serializers.ModelSerializer):
        
    class Meta:
        model = Term
        # fields = ("first_name", "last_name", "email", "account_number", "national_id", "gender", "created_at", "updated_at")
        fields = "__all__"


class UpdateTermSerializer(serializers.ModelSerializer):
        
        class Meta:
            model = Term
            fields = ("term_name",)
            # fields = "__all__"
        