from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from term.models import Term, TermCourse, RegistrationRequest
from term.serializers import TermCourseSerializer
from term.filters import TermCourseFilter
from term.permissions import IsITManagerOrEducationalAssistantWithSameFaculty, IsSameStudent
from rest_framework.response import Response
from rest_framework import status, generics, views, serializers
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
        elif student.years == 10 : # seventh validation
            raise PermissionDenied("You are not allowed to register for this term. Your year is full.")
        
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
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    def post(self, request, *args, **kwargs):
        student=Student.objects.get(id=self.kwargs.get('pk'))
        term=Term.objects.all().last()
        
        if not RegistrationRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You are ubable to access course selection. Invalid datetime range.")
        
        # serializer = CourseSelectionCheckSerializer(data=request.data, context={'pk': self.kwargs.get('pk')})
        # serializer.is_valid(raise_exception=True)
        
        # counting units of selected courses in the database
        units = 0
        for course in RegistrationRequest.objects.filter(term=term, student=student).first().courses.all() : 
            units += course.name.units
            
        if student.intrance_term == term :  # term avali
            if units < 20 :
                for pk in request.data['course'] : # counting units of selected courses in the request
                    data =  {'course' : [pk] ,'option': request.data['option']}
                    serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                    serializer.is_valid(raise_exception=True)
                    termcourse = TermCourse.objects.get(id=pk)
                    units += termcourse.name.units
                    if units > 20 :
                        raise serializers.ValidationError("You can not select more than 20 units.")
                return Response(serializer.data)
                
            raise serializers.ValidationError("You can not select more than 20 units.")
                    
        else :
            secondlast_term = Term.objects.all().reverse()[1]
            if student.term_score(secondlast_term) >= 17 :
                if units < 24 :
                    for pk in request.data['course'] : # counting units of selected courses in the request
                        data =  {'course' : [pk] ,'option': request.data['option']}
                        serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                        serializer.is_valid(raise_exception=True)
                        termcourse = TermCourse.objects.get(id=pk)
                        units += termcourse.name.units
                        if units > 24 :
                            raise serializers.ValidationError("You can not select more than 24 units.")
                    return Response(serializer.data)
                    
                raise serializers.ValidationError("You can not select more than 24 units.")
            
            else :
                if units < 20 :
                    for pk in request.data['course'] : # counting units of selected courses in the request
                        data =  {'course' : [pk] ,'option': request.data['option']}
                        serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                        serializer.is_valid(raise_exception=True)
                        termcourse = TermCourse.objects.get(id=pk)
                        units += termcourse.name.units
                        if units > 20 :
                            raise serializers.ValidationError("You can not select more than 20 units.")
                    return Response(serializer.data)
                    
                raise serializers.ValidationError("You can not select more than 20 units.")
        
        
        
    