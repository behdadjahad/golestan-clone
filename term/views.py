from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from term.models import Term, TermCourse, RegistrationRequest
from term.serializers import TermCourseSerializer
from term.filters import TermCourseFilter
from term.permissions import IsITManagerOrEducationalAssistantWithSameFaculty, IsSameStudent
from rest_framework.response import Response
from rest_framework import status, generics, views
from rest_framework.exceptions import PermissionDenied

from term.serializers import CourseSelectionSerializer, CourseSelectionCheckSerializer

from account.models import Student



class TermCourseViewSet(ModelViewSet) :
    serializer_class = TermCourseSerializer
    queryset = TermCourse.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = TermCourseFilter
    permission_classes = [IsAuthenticated ,IsITManagerOrEducationalAssistantWithSameFaculty]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, serializer.validated_data.get('name').faculty)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def get_object(self):
        course_id = self.kwargs.get('pk')
        termcourse =  TermCourse.objects.get(id=course_id)
        self.check_object_permissions(self.request, termcourse.name)
        return termcourse
    
    
class CourseSelectionCreationFormAPIView(generics.CreateAPIView) :
    serializer_class = CourseSelectionSerializer
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    def post(self, request, *args, **kwargs): # checking creation again
        student_id = self.kwargs.get('pk')
        student = Student.objects.get(id=student_id)
        self.check_object_permissions(self.request, student)
        term = Term.objects.all().last()
        if RegistrationRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You have already registered for this term.")
        return super().post(request, *args, **kwargs)
    
    
class CourseSelectionListAPIView(generics.ListAPIView) :
    # CourseSelectionListSerializer
    serializer_class = CourseSelectionSerializer
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    def get_queryset(self):
        student_id = self.kwargs.get('pk')
        student = Student.objects.get(id=student_id)
        self.check_object_permissions(self.request, student)
        term = Term.objects.all().last()
        return RegistrationRequest.objects.filter(term=term, student=student)
    
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data[0]
        response_data = {'status': 'success', 'courses': data['courses']}
        return Response(response_data)
    
    
class CourseSelectionCheckAPIView(views.APIView) :
    
    def post(self, request, *args, **kwargs):
        
        if not RegistrationRequest.objects.filter(term=Term.objects.all().last(), student=Student.objects.get(id=self.kwargs.get('pk'))).exists() :
            raise PermissionDenied("You are ubable to access course selection. Invalid datetime range.")
        
        serializer = CourseSelectionCheckSerializer(data=request.data, context={'pk': self.kwargs.get('pk')})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)