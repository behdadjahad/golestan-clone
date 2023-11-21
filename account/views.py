from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.views import APIView

from django.db.models import QuerySet

from faculty.models import Faculty

from django_filters.rest_framework import DjangoFilterBackend

from .models import Student, EducationalAssistant, Professor
from .serializers import *
from .permissions import  IsStudentOrEducationalAssistant, IsProfessorOrEducationalAssistant
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

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OutputFacultiesSerialiser
        else:
            return InputFacultiesSerialiser

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

    serializer_class = OutputFacultySerialiser

    # @extend_schema(responses=OutputFacultySerialiser)
    def get(self, request, id):

        try:
            query = self.get_faculty_detail(id=id)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(OutputFacultySerialiser(query, context={"request":request}).data)
    
    # @extend_schema(responses=OutputFacultySerialiser)
    def put(self, request, id):
        pass

    # @extend_schema(responses=OutputFacultySerialiser)
    def delete(self, request, id):
        try:
            query = self.delete_faculty(id=id)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(OutputFacultySerialiser(query, context={"request":request}).data)
    

    def get_faculty_detail(self, id:int) -> QuerySet[Faculty]:
        return Faculty.objects.get(id=id)

    def update_faculty(self) -> QuerySet[Faculty]:
        pass

    def delete_faculty(self, id:int) -> QuerySet[Faculty]:
        
        faculty = Faculty.objects.get(id=id)
        if faculty is None:
            raise Exception("There is no faculty with this id.")
        
        faculty.delete()
        