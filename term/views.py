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

from datetime import datetime

from django.db import transaction


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
        

        
        # counting units and date_time of selected courses in the database
        units = 0 # 5th validation
        date_and_times = {} # 6th validation
        for course in RegistrationRequest.objects.filter(term=term, student=student).first().courses.all() : 
            units += course.name.units
            
            for time in course.class_days_and_times :
                day = time['day']
                if day in date_and_times :
                    date_and_times[day].append((time['start_time'], time['end_time']))
                else :
                    date_and_times[day] = [(time['start_time'], time['end_time'])]
            
            
            
        if student.intrance_term == term :  # term avali
            if units < 20 :
                for pk in request.data['course'] : # counting units of selected courses in the request
                    data =  {'course' : [pk] ,'option': request.data['option']}
                    serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                    serializer.is_valid(raise_exception=True)
                    termcourse = TermCourse.objects.get(id=pk)
                    if data['option'] == 'add' :
                        units += termcourse.name.units
                        if units > 20 :
                            raise serializers.ValidationError("You can not select more than 20 units.")
                        
                        for time in termcourse.class_days_and_times :
                            day = time['day']
                            start_time = datetime.strptime(time['start_time'], "%H:%M")
                            end_time = datetime.strptime(time['end_time'], "%H:%M")
                            if day in date_and_times :
                                times_in_a_day = date_and_times[day]
                                for time_ in times_in_a_day :
                                    start = datetime.strptime(time_[0], "%H:%M")
                                    end = datetime.strptime(time_[1], "%H:%M")
                                    if (start_time < end and start_time > start) or (end_time > start and end_time < end) :
                                        raise serializers.ValidationError(f"the selected { termcourse } course interferes with previous courses")
                                date_and_times[day].append((time['start_time'], time['end_time']))
                                
                            else :
                                date_and_times[day] = [(time['start_time'], time['end_time'])]

            else :   
                raise serializers.ValidationError("You can not select more than 20 units.")
            
            return Response({"success": True}, status=200)
                 
                    
        else :
            secondlast_term = Term.objects.all().reverse()[1]
            if student.term_score(secondlast_term) >= 17 :
                if units < 24 :
                        for pk in request.data['course'] : # counting units of selected courses in the request
                            data =  {'course' : [pk] ,'option': request.data['option']}
                            serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                            serializer.is_valid(raise_exception=True)
                            termcourse = TermCourse.objects.get(id=pk)
                            if data['option'] == 'add' :
                                units += termcourse.name.units
                                if units > 24 :
                                    raise serializers.ValidationError("You can not select more than 20 units.")
                                
                                for time in termcourse.class_days_and_times :
                                    day = time['day']
                                    start_time = datetime.strptime(time['start_time'], "%H:%M")
                                    end_time = datetime.strptime(time['end_time'], "%H:%M")
                                    if day in date_and_times :
                                        times_in_a_day = date_and_times[day]
                                        for time_ in times_in_a_day :
                                            start = datetime.strptime(time_[0], "%H:%M")
                                            end = datetime.strptime(time_[1], "%H:%M")
                                            if (start_time < end and start_time > start) or (end_time > start and end_time < end) :
                                                raise serializers.ValidationError(f"the selected { termcourse } course interferes with previous courses")
                                        date_and_times[day].append((time['start_time'], time['end_time']))
                                        
                                    else :
                                        date_and_times[day] = [(time['start_time'], time['end_time'])]
   
                else :   
                    raise serializers.ValidationError("You can not select more than 24 units.")
                
                return Response({"success": True}, status=200)
            
            else :
                if units < 20 :
                    for pk in request.data['course'] : # counting units of selected courses in the request
                        data =  {'course' : [pk] ,'option': request.data['option']}
                        serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                        serializer.is_valid(raise_exception=True)
                        termcourse = TermCourse.objects.get(id=pk)
                        if data['option'] == 'add' :
                            units += termcourse.name.units
                            if units > 20 :
                                raise serializers.ValidationError("You can not select more than 20 units.")
                            
                            for time in termcourse.class_days_and_times :
                                day = time['day']
                                start_time = datetime.strptime(time['start_time'], "%H:%M")
                                end_time = datetime.strptime(time['end_time'], "%H:%M")
                                if day in date_and_times :
                                    times_in_a_day = date_and_times[day]
                                    for time_ in times_in_a_day :
                                        start = datetime.strptime(time_[0], "%H:%M")
                                        end = datetime.strptime(time_[1], "%H:%M")
                                        if (start_time < end and start_time > start) or (end_time > start and end_time < end) :
                                            raise serializers.ValidationError(f"the selected { termcourse } course interferes with previous courses")
                                    date_and_times[day].append((time['start_time'], time['end_time']))
                                    
                                else :
                                    date_and_times[day] = [(time['start_time'], time['end_time'])]
                else :   
                    raise serializers.ValidationError("You can not select more than 20 units.")
                
                return Response({"success": True}, status=200)
        
        
        
        
class CourseSelectionSubmitAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        student=Student.objects.get(id=self.kwargs.get('pk'))
        term=Term.objects.all().last()
        registration_request = RegistrationRequest.objects.filter(term=term, student=student).first()
        
        if not RegistrationRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You are ubable to access course selection. Invalid datetime range.")
        
        
        # counting units and date_time of selected courses in the database
        units = 0 # 5th validation
        date_and_times = {} # 6th validation
        for course in RegistrationRequest.objects.filter(term=term, student=student).first().courses.all() : 
            units += course.name.units
            
            for time in course.class_days_and_times :
                day = time['day']
                if day in date_and_times :
                    date_and_times[day].append((time['start_time'], time['end_time']))
                else :
                    date_and_times[day] = [(time['start_time'], time['end_time'])]
            
            
            
        if student.intrance_term == term :  # term avali
            try :
                if units < 20 :
                    for pk in request.data['course'] : # counting units of selected courses in the request
                        data =  {'course' : [pk] ,'option': request.data['option']}
                        serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                        serializer.is_valid(raise_exception=True)
                        termcourse = TermCourse.objects.get(id=pk)
                        if data['option'] == 'add' :
                            units += termcourse.name.units
                            if units > 20 :
                                raise serializers.ValidationError("You can not select more than 20 units.")
                            
                            for time in termcourse.class_days_and_times :
                                day = time['day']
                                start_time = datetime.strptime(time['start_time'], "%H:%M")
                                end_time = datetime.strptime(time['end_time'], "%H:%M")
                                if day in date_and_times :
                                    times_in_a_day = date_and_times[day]
                                    for time_ in times_in_a_day :
                                        start = datetime.strptime(time_[0], "%H:%M")
                                        end = datetime.strptime(time_[1], "%H:%M")
                                        if (start_time < end and start_time > start) or (end_time > start and end_time < end) :
                                            raise serializers.ValidationError(f"the selected { termcourse } course interferes with previous courses")
                                    date_and_times[day].append((time['start_time'], time['end_time']))
                                    
                                else :
                                    date_and_times[day] = [(time['start_time'], time['end_time'])]
                 
                            registration_request.courses.add(termcourse)
                                
                        elif data['option'] == 'delete' :    
                            registration_request.courses.remove(termcourse)
                else :   
                    raise serializers.ValidationError("You can not select more than 20 units.")
                
                return Response({"success": True}, status=200)
            
            except Exception as e : # we can add logging logic here
                print(e)
                raise e
                    
                    
        else :
            secondlast_term = Term.objects.all().reverse()[1]
            if student.term_score(secondlast_term) >= 17 :
                try :
                    if units < 24 :
                        for pk in request.data['course'] : # counting units of selected courses in the request
                            data =  {'course' : [pk] ,'option': request.data['option']}
                            serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                            serializer.is_valid(raise_exception=True)
                            termcourse = TermCourse.objects.get(id=pk)
                            if data['option'] == 'add' :
                                units += termcourse.name.units
                                if units > 24 :
                                    raise serializers.ValidationError("You can not select more than 20 units.")
                                
                                for time in termcourse.class_days_and_times :
                                    day = time['day']
                                    start_time = datetime.strptime(time['start_time'], "%H:%M")
                                    end_time = datetime.strptime(time['end_time'], "%H:%M")
                                    if day in date_and_times :
                                        times_in_a_day = date_and_times[day]
                                        for time_ in times_in_a_day :
                                            start = datetime.strptime(time_[0], "%H:%M")
                                            end = datetime.strptime(time_[1], "%H:%M")
                                            if (start_time < end and start_time > start) or (end_time > start and end_time < end) :
                                                raise serializers.ValidationError(f"the selected { termcourse } course interferes with previous courses")
                                        date_and_times[day].append((time['start_time'], time['end_time']))
                                        
                                    else :
                                        date_and_times[day] = [(time['start_time'], time['end_time'])]
                    
                                registration_request.courses.add(termcourse)
                                    
                            elif data['option'] == 'delete' :    
                                registration_request.courses.remove(termcourse)
                    else :   
                        raise serializers.ValidationError("You can not select more than 24 units.")
                    
                    return Response({"success": True}, status=200)
                
                except Exception as e : # we can add logging logic here
                    print(e)
                    raise e
                
            
            else :
                try :
                    if units < 20 :
                        for pk in request.data['course'] : # counting units of selected courses in the request
                            data =  {'course' : [pk] ,'option': request.data['option']}
                            serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                            serializer.is_valid(raise_exception=True)
                            termcourse = TermCourse.objects.get(id=pk)
                            if data['option'] == 'add' :
                                units += termcourse.name.units
                                if units > 20 :
                                    raise serializers.ValidationError("You can not select more than 20 units.")
                                
                                for time in termcourse.class_days_and_times :
                                    day = time['day']
                                    start_time = datetime.strptime(time['start_time'], "%H:%M")
                                    end_time = datetime.strptime(time['end_time'], "%H:%M")
                                    if day in date_and_times :
                                        times_in_a_day = date_and_times[day]
                                        for time_ in times_in_a_day :
                                            start = datetime.strptime(time_[0], "%H:%M")
                                            end = datetime.strptime(time_[1], "%H:%M")
                                            if (start_time < end and start_time > start) or (end_time > start and end_time < end) :
                                                raise serializers.ValidationError(f"the selected { termcourse } course interferes with previous courses")
                                        date_and_times[day].append((time['start_time'], time['end_time']))
                                        
                                    else :
                                        date_and_times[day] = [(time['start_time'], time['end_time'])]
                    
                                registration_request.courses.add(termcourse)
                                    
                            elif data['option'] == 'delete' :    
                                registration_request.courses.remove(termcourse)
                    else :   
                        raise serializers.ValidationError("You can not select more than 20 units.")
                    
                    return Response({"success": True}, status=200)
                
                except Exception as e : # we can add logging logic here
                    print(e)
                    raise e