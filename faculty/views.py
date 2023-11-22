from rest_framework import generics, filters, views, response, status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from account.models import EducationalAssistant
from faculty.permissions import IsITManagerOrEducationalAssistantWithSameFaculty
from faculty.serializers import ApprovedCourseSerializer, FacultySerializer
from faculty.models import ApprovedCourse, Faculty
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView


class FacultyViewSet(ModelViewSet) :
    serializer_class = FacultySerializer
    queryset = Faculty.objects.all()
    permission_classes = [AllowAny]
    
    

class ApprovedCourseViewSet(ModelViewSet) :
    serializer_class = ApprovedCourseSerializer
    queryset = ApprovedCourse.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['faculty', 'course_name']
    permission_classes = [IsAuthenticated, IsITManagerOrEducationalAssistantWithSameFaculty]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.check_object_permissions(self.request, serializer.validated_data.get('faculty'))
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_object(self):
        course_id = self.kwargs.get('pk')
        course = ApprovedCourse.objects.get(id=course_id)
        self.check_object_permissions(self.request, course)
        return course

