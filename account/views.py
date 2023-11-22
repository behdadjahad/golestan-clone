from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.views import APIView

from django.db.models import QuerySet

from faculty.models import Faculty, Major

from django_filters.rest_framework import DjangoFilterBackend

from .models import Student, EducationalAssistant, Professor
from .serializers import *
from .permissions import *
from .filters import StudentFilter, ProfessorFilter
from term.models import TermCourse

# from drf_spectacular.utils import extend_schema

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = StudentFilter
    permission_classes = [IsAuthenticated, IsStudentOrEducationalAssistant]
    allowed_methods = ['GET', 'PUT']
    
    def list(self, request, *args, **kwargs):
        username = self.request.user.username
        if Student.objects.filter(username=username).exists():
            raise PermissionDenied("You do not have permission to perform this action.")
        
        eda = EducationalAssistant.objects.get(username=username)
        student = Student.objects.filter(faculty=eda.faculty)
        serializer = StudentSerializer(student, many=True)
        return Response(serializer.data)    

    def get_object(self):
        student_id = self.kwargs.get('pk')
        student = Student.objects.get(id=student_id) 
        self.check_object_permissions(self.request, student)
        return student
    
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
          
  
    
class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProfessorFilter
    permission_classes = [IsAuthenticated, IsProfessorOrEducationalAssistant]
    allowed_methods = ['GET', 'PUT']
    
    def list(self, request, *args, **kwargs):
        username = self.request.user.username
        if Professor.objects.filter(username=username).exists():
            raise PermissionDenied("You do not have permission to perform this action.")
   
        eda = EducationalAssistant.objects.get(username=username)
        professor = Professor.objects.filter(faculty=eda.faculty)
        serializer = ProfessorSerializer(professor, many=True)
        return Response(serializer.data)
        

    def get_object(self):
        professor_id = self.kwargs.get('pk')
        professor = Professor.objects.get(id=professor_id) 
        self.check_object_permissions(self.request, professor)
        return Professor.objects.get(id=professor_id)
    
    
class StudentClassScheduleView(ListAPIView) :
    serializer_class = StudentClassScheduleSerializer
    
    def get_queryset(self) :
        username = self.request.user.username
        if Student.objects.filter(username=username).exists():
            student = Student.objects.get(username=username)
            active_course = student.active_courses
            return active_course
        
class StudentExamScheduleView(ListAPIView) :
    serializer_class = StudentExamScheduleSerializer
    
    def get_queryset(self) :
        username = self.request.user.username
        if Student.objects.filter(username=username).exists():
            student = Student.objects.get(username=username)
            active_course = student.active_courses
            return active_course

class FacultyApi(APIView):


    # class Pagination(LimitOffsetPagination):
    #     pass

    serializer_class = InputFacultiesSerialiser
    permission_classes = [IsAuthenticated, IsItManager]


    def get_serializer_class(self):
        if self.request.method == "POST":
            return InputFacultiesSerialiser
        else:
            return OutputProfessorsSerialiser

    # @extend_schema(request=InputFacultiesSerialiser, responses=OutputFacultiesSerialiser)
    def post(self, request):
        
        serializer = InputFacultiesSerialiser(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            query = self.create_faculty(name=serializer.validated_data.get("name"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)

        return Response(OutputFacultiesSerialiser(query, context={"request":request}).data)
    
    # @extend_schema(responses=OutputFacultiesSerialiser)
    def get(self, request):
        query = self.get_faculties()
        return Response(OutputFacultiesSerialiser(query, context={"request":request}, many=True).data)


    def create_faculty(self, name:str)-> QuerySet[Faculty]:
        
        return Faculty.objects.create(name=name)


    def get_faculties(self) -> QuerySet[Faculty]:
        return Faculty.objects.all()


class FacultyDetailApi(APIView):

    serializer_class = UpdateFacultySerializer
    permission_classes = [IsAuthenticated, IsItManager]


    # @extend_schema(responses=OutputFacultySerialiser)
    def get(self, request, pk):

        try:
            query = self.get_faculty_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateFacultySerializer(query, context={"request":request}).data)
    
    # @extend_schema(responses=UpdateFacultySerializer)
    def put(self, request, pk):
        try:
            query = self.get_faculty_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}", status=status.HTTP_400_BAD_REQUEST)
        serializer = UpdateFacultySerializer(query, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @extend_schema(responses=UpdateFacultySerializer)
    def delete(self, request, pk):
        try:
            query = self.delete_faculty(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateFacultySerializer(query, context={"request":request}).data)
    

    def get_faculty_detail(self, pk:int) -> QuerySet[Faculty]:
        return Faculty.objects.get(pk=pk)


    def delete_faculty(self, pk:int) -> QuerySet[Faculty]:
        
        faculty = Faculty.objects.get(pk=pk)
        if faculty is None:
            raise Exception("There is no faculty with this id.")
        
        faculty.delete()


class ProfessorApi(APIView):

    # class Pagination(LimitOffsetPagination):
    #     pass
    serializer_class = InputProfessorsSerialiser
    permission_classes = [IsAuthenticated, IsItManager]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InputProfessorsSerialiser
        else:
            return OutputProfessorsSerialiser

    # @extend_schema(request=InputProfessorsSerialiser, responses=OutputProfessorsSerialiser)
    def post(self, request):
        
        serializer = InputProfessorsSerialiser(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            query = self.create_professor(first_name=serializer.validated_data.get("first_name"),
                                     last_name=serializer.validated_data.get("last_name"),
                                     account_number=serializer.validated_data.get("account_number"),
                                     phone_number=serializer.validated_data.get("phone_number"),
                                     national_id=serializer.validated_data.get("national_id"),
                                     birth_date=serializer.validated_data.get("birth_date"),
                                     gender=serializer.validated_data.get("gender"),
                                     email=serializer.validated_data.get("email"),
                                     password=serializer.validated_data.get("password"),
                                     faculty=serializer.validated_data.get("faculty"),
                                     major=serializer.validated_data.get("major"),
                                     expertise=serializer.validated_data.get("expertise"),
                                     degree=serializer.validated_data.get("degree"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)

        return Response(OutputProfessorsSerialiser(query, context={"request":request}).data)
    
    # @extend_schema(responses=OutputProfessorsSerialiser)
    def get(self, request):
        query = self.get_professors()
        return Response(OutputProfessorsSerialiser(query, context={"request":request}, many=True).data)
    
    def create_professor(self,
                     first_name:str,
                     last_name:str,
                     account_number:str,
                     phone_number:str,
                     national_id:str,
                     birth_date,
                     gender:str,
                     email:str,
                     password:str,
                     faculty:int,
                     major:int,
                     expertise:str,
                     degree:str)-> QuerySet[Professor]:
    

        major_object = Major.objects.get(id=major)
        if  major_object is None:
            raise Exception("There is no major with this id.")

        faculty_object = Faculty.objects.get(id=faculty)
        if faculty_object is None:
            raise Exception("There is no faculty with this id.")
        

        return Professor.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            account_number=account_number,
            national_id=national_id,
            birth_date=birth_date,
            gender=gender,
            email=email,
            password=password,
            faculty=faculty_object,
            major=major_object,
            expertise=expertise,
            degree=degree)


    def get_professors(self) -> QuerySet[Professor]:
        return Professor.objects.all()


class ProfessorDetailApi(APIView):
        
    serializer_class = UpdateProfessorSerialiser
    permission_classes = [IsAuthenticated, IsItManager]

    # @extend_schema(responses=UpdateProfessorSerialiser)
    def get(self, request, pk):

        try:
            query = self.get_professor_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateProfessorSerialiser(query, context={"request":request}).data)
    
    # @extend_schema(responses=UpdateProfessorSerialiser)
    def put(self, request, pk):
        try:
            query = self.get_professor_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}", status=status.HTTP_400_BAD_REQUEST)
        serializer = UpdateProfessorSerialiser(query, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    # @extend_schema(responses=UpdateProfessorSerialiser)
    def delete(self, request, pk):
        try:
            query = self.delete_professor(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        return Response(UpdateProfessorSerialiser(query, context={"request":request}).data)
    
    def get_professor_detail(self, pk:int) -> QuerySet[Professor]:
        return Professor.objects.get(pk=pk)

    def delete_professor(self, pk:int) -> QuerySet[Professor]:
        
        professor = Professor.objects.get(pk=pk)
        if professor is None:
            raise Exception("There is no prfessor with this id.")
        
        professor.delete()


class StudentApi(APIView):

    serializer_class = InputStudentsSerialiser
    permission_classes = [IsAuthenticated, IsItManager]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InputStudentsSerialiser
        else:
            return OutputStudentsSerialiser

    # class Pagination(LimitOffsetPagination):
    #     pass
    # @extend_schema(request=InputStudentsSerialiser, responses=OutputStudentsSerialiser)
    def post(self, request):
        
        serializer = InputStudentsSerialiser(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            query = self.create_student(first_name=serializer.validated_data.get("first_name"),
                                   last_name=serializer.validated_data.get("last_name"),
                                   account_number=serializer.validated_data.get("account_number"),
                                   phone_number=serializer.validated_data.get("phone_number"),
                                   national_id=serializer.validated_data.get("national_id"),
                                   birth_date=serializer.validated_data.get("birth_date"),
                                   gender=serializer.validated_data.get("gender"),
                                   military_service_status=serializer.validated_data.get("military_service_status"),
                                   entrance_year=serializer.validated_data.get("entrance_year"),
                                   entrance_term=serializer.validated_data.get("entrance_term"),
                                   email=serializer.validated_data.get("email"),
                                   password=serializer.validated_data.get("password"),
                                   faculty=serializer.validated_data.get("faculty"),
                                   major=serializer.validated_data.get("major"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)

        return Response(OutputStudentsSerialiser(query, context={"request":request}).data)
    
    # @extend_schema(responses=OutputStudentsSerialiser)
    def get(self, request):
        query = self.get_students()
        return Response(OutputStudentsSerialiser(query, context={"request":request}, many=True).data)
    
    def create_student(self,
                   first_name:str,
                   last_name:str,
                   account_number:str,
                   phone_number:str,
                   national_id:str,
                   birth_date,
                   gender:str,
                   military_service_status:str,
                   entrance_year,
                   entrance_term:str,
                   email:str,
                   password:str,
                   faculty:int,
                   major:int
                   )-> QuerySet[Student]:
    

        major_object = Major.objects.get(id=major)
        if  major_object is None:
            raise Exception("There is no major with this id.")

        faculty_object = Faculty.objects.get(id=faculty)
        if faculty_object is None:
            raise Exception("There is no faculty with this id.")
        

        return Student.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            account_number=account_number,
            national_id=national_id,
            birth_date=birth_date,
            gender=gender,
            military_service_status=military_service_status,
            entrance_year=entrance_year,
            entrance_term=entrance_term,
            email=email,
            password=password,
            faculty=faculty_object,
            major=major_object)


    def get_students(self) -> QuerySet[Student]:
        return Student.objects.all()


class StudentDetailApi(APIView):

    serializer_class = UpdateStudentSerializer
    permission_classes = [IsAuthenticated, IsItManager]

    # @extend_schema(responses=UpdateStudentSerializer)
    def get(self, request, pk):

        try:
            query = self.get_student_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateStudentSerializer(query, context={"request":request}).data)
    
    # @extend_schema(responses=UpdateStudentSerializer)
    def put(self, request, pk):
        try:
            query = self.get_student_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}", status=status.HTTP_400_BAD_REQUEST)
        serializer = UpdateStudentSerializer(query, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # @extend_schema(responses=UpdateStudentSerializer)
    def delete(self, request, pk):
        try:
            query = self.delete_student(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateStudentSerializer(query, context={"request":request}).data)

    def get_student_detail(self, pk:int) -> QuerySet[Student]:
        return Student.objects.get(pk=pk)

    def delete_student(self, pk:int) -> QuerySet[Student]:
        
        student = Student.objects.get(pk=pk)
        if student is None:
            raise Exception("There is no student with this id.")
        
        student.delete()


class AssistantApi(APIView):

    serializer_class = InputAssistantsSerialiser
    permission_classes = [IsAuthenticated, IsItManager]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InputAssistantsSerialiser
        else:
            return OutputAsistantsSerialiser

    # class Pagination(LimitOffsetPagination):
    #     pass


    # @extend_schema(request=InputAssistantsSerialiser, responses=OutputAsistantsSerialiser)
    def post(self, request):
        
        serializer = InputAssistantsSerialiser(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            query = self.create_assistant(first_name=serializer.validated_data.get("first_name"),
                                     last_name=serializer.validated_data.get("last_name"),
                                     account_number=serializer.validated_data.get("account_number"),
                                     phone_number=serializer.validated_data.get("phone_number"),
                                     national_id=serializer.validated_data.get("national_id"),
                                     birth_date=serializer.validated_data.get("birth_date"),
                                     gender=serializer.validated_data.get("gender"),
                                     email=serializer.validated_data.get("email"),
                                     password=serializer.validated_data.get("password"),
                                     faculty=serializer.validated_data.get("faculty"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)

        return Response(OutputAsistantsSerialiser(query, context={"request":request}).data)
    
    # @extend_schema(responses=OutputAsistantsSerialiser)
    def get(self, request):
        query = self.get_assistants()
        return Response(OutputAsistantsSerialiser(query, context={"request":request}, many=True).data)
    
    def create_assistant(self,
                   first_name:str,
                   last_name:str,
                   account_number:str,
                   phone_number:str,
                   national_id:str,
                   birth_date,
                   gender:str,
                   email:str,
                   password:str,
                   faculty:int,)-> QuerySet[EducationalAssistant]:
    

        faculty_object = Faculty.objects.get(id=faculty)
        if faculty_object is None:
            raise Exception("There is no faculty with this id.")
        

        return EducationalAssistant.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            account_number=account_number,
            national_id=national_id,
            birth_date=birth_date,
            gender=gender,
            email=email,
            password=password,
            faculty=faculty_object)


    def get_assistants(self) -> QuerySet[EducationalAssistant]:
        return EducationalAssistant.objects.all()

class AsistantDetailApi(APIView):

    serializer_class = UpdateAssistantSerializer
    permission_classes = [IsAuthenticated, IsItManager]

    # @extend_schema(responses=UpdateAssistantSerializer)
    def get(self, request, pk):

        try:
            query = self.get_assistant_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateAssistantSerializer(query, context={"request":request}).data)
    
    # @extend_schema(responses=UpdateAssistantSerializer)
    def put(self, request, pk):
        try:
            query = self.get_assistant_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}", status=status.HTTP_400_BAD_REQUEST)
        serializer = UpdateAssistantSerializer(query, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    # @extend_schema(responses=UpdateAssistantSerializer)
    def delete(self, request, pk):
        try:
            query = self.delete_assistant(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateAssistantSerializer(query, context={"request":request}).data)
    
    def get_assistant_detail(self, pk:int) -> QuerySet[EducationalAssistant]:
        return EducationalAssistant.objects.get(pk=pk)

    def delete_assistant(self, pk:int) -> QuerySet[EducationalAssistant]:
        
        assistant = EducationalAssistant.objects.get(pk=pk)
        if assistant is None:
            raise Exception("There is no assitant with this id.")
        
        assistant.delete()


class TermsApi(APIView):
    
    serializer_class = InputTermsSerialiser
    permission_classes = [IsAuthenticated, IsItManager]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InputTermsSerialiser
        else:
            return OutputTermsSerialiser

    # class Pagination(LimitOffsetPagination):
    #     pass


    # @extend_schema(request=InputTermsSerialiser, responses=OutputTermsSerialiser)
    def post(self, request):
        
        serializer = InputTermsSerialiser(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            query = self.create_term(term_name=serializer.validated_data.get("term_name"),
                                unit_selection_start_time=serializer.validated_data.get("unit_selection_start_time"),
                                unit_selection_end_time=serializer.validated_data.get("unit_selection_end_time"),
                                courses_start_time=serializer.validated_data.get("courses_start_time"),
                                courses_end_time=serializer.validated_data.get("courses_end_time"),
                                repairing_unit_selection_start_time=serializer.validated_data.get("repairing_unit_selection_start_time"),
                                repairing_unit_selection_end_time=serializer.validated_data.get("repairing_unit_selection_end_time"),
                                emergency_deletion_start_time=serializer.validated_data.get("emergency_deletion_start_time") ,
                                emergency_deletion_end_time=serializer.validated_data.get("emergency_deletion_end_time"),
                                exams_start_time=serializer.validated_data.get("exams_start_time"),
                                term_end_time=serializer.validated_data.get("term_end_time"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)

        return Response(OutputTermsSerialiser(query, context={"request":request}).data)
    
    # @extend_schema(responses=OutputTermsSerialiser)
    def get(self, request):
        query = self.get_terms()
        return Response(OutputTermsSerialiser(query, context={"request":request}, many=True).data)
    
    def create_term(self,
                term_name:str,
                unit_selection_start_time,
                unit_selection_end_time,
                courses_start_time,
                courses_end_time,
                repairing_unit_selection_start_time,
                repairing_unit_selection_end_time,
                emergency_deletion_start_time,
                emergency_deletion_end_time,
                exams_start_time,
                term_end_time)-> QuerySet[Term]:
    
        return Term.objects.create(
            term_name=term_name,
            unit_selection_start_time=unit_selection_start_time,
            unit_selection_end_time=unit_selection_end_time,
            courses_start_time=courses_start_time,
            courses_end_time=courses_end_time,
            repairing_unit_selection_start_time=repairing_unit_selection_start_time,
            repairing_unit_selection_end_time=repairing_unit_selection_end_time,
            emergency_deletion_start_time=emergency_deletion_start_time,
            emergency_deletion_end_time=emergency_deletion_end_time,
            exams_start_time=exams_start_time,
            term_end_time=term_end_time)

    def get_terms(self) -> QuerySet[Term]:
        return Term.objects.all()

class TermDetailApi(APIView):

    serializer_class = UpdateTermSerializer
    permission_classes = [IsAuthenticated, IsItManager]
    
    # @extend_schema(responses=UpdateTermSerializer)
    def get(self, request, pk):

        try:
            query = self.get_term_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateTermSerializer(query, context={"request":request}).data)
    
    # @extend_schema(responses=UpdateTermSerializer)
    def put(self, request, pk):
        try:
            query = self.get_term_detail(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}", status=status.HTTP_400_BAD_REQUEST)
        serializer = UpdateTermSerializer(query, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # @extend_schema(responses=UpdateTermSerializer)
    def delete(self, request, pk):
        try:
            query = self.delete_term(pk=pk)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(UpdateTermSerializer(query, context={"request":request}).data)
    
    def get_term_detail(self, pk:int) -> QuerySet[Term]:
        return Term.objects.get(pk=pk)

    def delete_term(self, pk:int) -> QuerySet[Term]:
        
        term = Term.objects.get(pk=pk)
        if term is None:
            raise Exception("There is no term with this id.")
        
        term.delete()
    

        