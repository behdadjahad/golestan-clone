from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from term.models import Term, TermCourse, RegistrationRequest, CourseStudent, RemovalAndExtensionRequest
from term.serializers import CourseSubstitutionCheckSerializer, TermCourseSerializer
from term.filters import TermCourseFilter
from term.permissions import IsITManagerOrEducationalAssistantWithSameFaculty, IsSameStudent, IsSameProfessor
from rest_framework.response import Response
from rest_framework import status, generics, views, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from term.serializers import *

from account.models import Professor, Student

from datetime import datetime, timedelta

from django.db import transaction
from .models import CourseStudent, ReconsiderationRequest


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
    
    def create(self, request, *args, **kwargs):
        data = {"student": self.kwargs.get('pk'), "term": Term.objects.all().last().id}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    
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
        if len(serializer.data) == 0 :
            raise PermissionDenied("You have not registered for this term.")
        else :
            data = serializer.data[0]
            response_data = {'status': data['confirmation_status'], 'courses': data['courses']}
            return Response(response_data)
    
    
class CourseSelectionCheckAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameStudent]
    

    def post(self, request, *args, **kwargs):
        student=Student.objects.get(id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, student)
        term=Term.objects.all().last()
        registration_request = RegistrationRequest.objects.filter(term=term, student=student).first()
        
        if not RegistrationRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You have not registered for this term.")
        elif registration_request.confirmation_status == 'confirmed' :
            raise PermissionDenied("Your registration request confirmed. You can not change it again.") 
        elif registration_request.confirmation_status == 'Waiting' :
            raise PermissionDenied("You have already sended your registration request. Please wait for confirmation.")
        
        
        # counting units and date_time of selected courses in the database
        units = 0 # 5th validation
        date_and_times = {} # 6th validation
        exams_time = []
        for course in RegistrationRequest.objects.filter(term=term, student=student).first().courses.all() : 
            units += course.name.units
            
            for time in course.class_days_and_times :
                day = time['day']
                if day in date_and_times :
                    date_and_times[day].append((time['start_time'], time['end_time']))
                else :
                    date_and_times[day] = [(time['start_time'], time['end_time'])]
                    
            start = datetime(course.exam_time.year, course.exam_time.month, course.exam_time.day, course.exam_time.hour, course.exam_time.minute)
            end = start + timedelta(hours=2)
            exams_time.append((start, end))
            
            
        if student.intrance_term == term :  # term avali
            for pk in request.data['course'] : # counting units of selected courses in the request
                data =  {'course' : [pk] ,'option': request.data['option']}
                serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                serializer.is_valid(raise_exception=True)
                termcourse = TermCourse.objects.get(id=pk)
                if data['option'] == 'add' :
                    units += termcourse.name.units
                    if units >= 20 :
                        raise serializers.ValidationError("You can not select more than 20 units.")
                    elif termcourse.course_capacity == 0 :
                        raise serializers.ValidationError("The selected course is full.")
                    
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
                        
                    
                    start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                    end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                    for exam_time in exams_time :
                        start = exam_time[0]
                        end = exam_time[1]
                        if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                            raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                    exams_time.append((start_added_exam_time, end_added_exam_time))
                    
                elif data['option'] == 'delete' :
                    units -= termcourse.name.units
                    
                    for time in termcourse.class_days_and_times :
                        day = time['day']
                        date_and_times[day].remove((time['start_time'], time['end_time']))
                    
                    start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                    end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                    for exam_time in exams_time :
                        start = exam_time[0]
                        end = exam_time[1]
                        exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
            
            return Response({"success": True}, status=200)
                 
                    
                    
        else :
            secondlast_term = Term.objects.all().reverse()[1]
            if student.term_score(secondlast_term) >= 17 :

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
                        
                        start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                        exams_time.append((start_added_exam_time, end_added_exam_time))
                    elif data['option'] == 'delete' :
                        units -= termcourse.name.units
                        
                        for time in termcourse.class_days_and_times :
                            day = time['day']
                            date_and_times[day].remove((time['start_time'], time['end_time']))
                        
                        start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
   
                
                return Response({"success": True}, status=200)
            
            else :
                for pk in request.data['course'] : # counting units of selected courses in the request
                    data =  {'course' : [pk] ,'option': request.data['option']}
                    serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                    serializer.is_valid(raise_exception=True)
                    termcourse = TermCourse.objects.get(id=pk)
                    if data['option'] == 'add' :
                        units += termcourse.name.units
                        if units >= 20 :
                            raise serializers.ValidationError("You can not select more than 20 units.")
                        elif termcourse.course_capacity == 0 :
                            raise serializers.ValidationError("The selected course is full.")
                        
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
                            
                        
                        start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                        exams_time.append((start_added_exam_time, end_added_exam_time))
                        
                    elif data['option'] == 'delete' :
                        units -= termcourse.name.units
                        
                        for time in termcourse.class_days_and_times :
                            day = time['day']
                            date_and_times[day].remove((time['start_time'], time['end_time']))
                        
                        start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
                
                return Response({"success": True}, status=200)
        
        
        
        
class CourseSelectionSubmitAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        student=Student.objects.get(id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, student)
        term=Term.objects.all().last()
        registration_request = RegistrationRequest.objects.filter(term=term, student=student).first()
        
        if not RegistrationRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You have not registered for this term.")
        elif registration_request.confirmation_status == 'confirmed' :
            raise PermissionDenied("Your registration request confirmed. You can not change it again.") 
        elif registration_request.confirmation_status == 'Waiting' :
            raise PermissionDenied("You have already sended your registration request. Please wait for confirmation.")
        
        
        # counting units and date_time of selected courses in the database
        units = 0 # 5th validation
        date_and_times = {} # 6th validation
        exams_time = []
        for course in RegistrationRequest.objects.filter(term=term, student=student).first().courses.all() : 
            units += course.name.units
            
            for time in course.class_days_and_times :
                day = time['day']
                if day in date_and_times :
                    date_and_times[day].append((time['start_time'], time['end_time']))
                else :
                    date_and_times[day] = [(time['start_time'], time['end_time'])]
                    
            start = datetime(course.exam_time.year, course.exam_time.month, course.exam_time.day, course.exam_time.hour, course.exam_time.minute)
            end = start + timedelta(hours=2)
            exams_time.append((start, end))
            
            
            
        if student.intrance_term == term :  # term avali
            try :   
                for pk in request.data['course'] : # counting units of selected courses in the request
                    data =  {'course' : [pk] ,'option': request.data['option']}
                    serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                    serializer.is_valid(raise_exception=True)
                    termcourse = TermCourse.objects.get(id=pk)
                    if data['option'] == 'add' :
                        units += termcourse.name.units
                        if units >= 20 :
                            raise serializers.ValidationError("You can not select more than 20 units.")
                        elif termcourse.course_capacity == 0 :
                            raise serializers.ValidationError("The selected course is full.")
                        
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
                                
                        start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                        exams_time.append((start_added_exam_time, end_added_exam_time))
                            
                        termcourse.course_capacity -= 1
                        termcourse.save()
                        registration_request.courses.add(termcourse)
                            
                    elif data['option'] == 'delete' :    
                        units -= termcourse.name.units
                        for time in termcourse.class_days_and_times :
                            day = time['day']
                            date_and_times[day].remove((time['start_time'], time['end_time']))
                        
                        start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
                        
                        termcourse.course_capacity += 1
                        termcourse.save()
                        registration_request.courses.remove(termcourse)
                            
                return Response({"success": True}, status=200)
            
            except Exception as e : # we can add logging logic here
                print(e)
                raise e
                    
                    
        else :
            secondlast_term = Term.objects.all().reverse()[1]
            if student.term_score(secondlast_term) >= 17 :
                try :
                    for pk in request.data['course'] : # counting units of selected courses in the request
                        data =  {'course' : [pk] ,'option': request.data['option']}
                        serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                        serializer.is_valid(raise_exception=True)
                        termcourse = TermCourse.objects.get(id=pk)
                        if data['option'] == 'add' :
                            units += termcourse.name.units
                            if units >= 24 :
                                raise serializers.ValidationError("You can not select more than 24 units.")
                            elif termcourse.course_capacity == 0 :
                                raise serializers.ValidationError("The selected course is full.")
                            
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
                                    
                            start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                            end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                            for exam_time in exams_time :
                                start = exam_time[0]
                                end = exam_time[1]
                                if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                    raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                            exams_time.append((start_added_exam_time, end_added_exam_time))
                                
                            termcourse.course_capacity -= 1
                            termcourse.save()
                            registration_request.courses.add(termcourse)
                                
                        elif data['option'] == 'delete' :    
                            units -= termcourse.name.units
                            for time in termcourse.class_days_and_times :
                                day = time['day']
                                date_and_times[day].remove((time['start_time'], time['end_time']))
                            
                            start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                            end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                            for exam_time in exams_time :
                                start = exam_time[0]
                                end = exam_time[1]
                                exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
                            
                            termcourse.course_capacity += 1
                            termcourse.save()
                            registration_request.courses.remove(termcourse)
                    
                    return Response({"success": True}, status=200)
                
                except Exception as e : # we can add logging logic here
                    print(e)
                    raise e
                
            
            else :
                try :
                    for pk in request.data['course'] : # counting units of selected courses in the request
                        data =  {'course' : [pk] ,'option': request.data['option']}
                        serializer = CourseSelectionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                        serializer.is_valid(raise_exception=True)
                        termcourse = TermCourse.objects.get(id=pk)
                        if data['option'] == 'add' :
                            units += termcourse.name.units
                            if units >= 20 :
                                raise serializers.ValidationError("You can not select more than 20 units.")
                            elif termcourse.course_capacity == 0 :
                                raise serializers.ValidationError("The selected course is full.")
                            
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
                                    
                            start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                            end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                            for exam_time in exams_time :
                                start = exam_time[0]
                                end = exam_time[1]
                                if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                    raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                            exams_time.append((start_added_exam_time, end_added_exam_time))
                                
                            termcourse.course_capacity -= 1
                            termcourse.save()
                            registration_request.courses.add(termcourse)
                                
                        elif data['option'] == 'delete' :    
                            units -= termcourse.name.units
                            for time in termcourse.class_days_and_times :
                                day = time['day']
                                date_and_times[day].remove((time['start_time'], time['end_time']))
                            
                            start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                            end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                            for exam_time in exams_time :
                                start = exam_time[0]
                                end = exam_time[1]
                                exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
                            
                            termcourse.course_capacity += 1
                            termcourse.save()
                            registration_request.courses.remove(termcourse)
                    
                    return Response({"success": True}, status=200)
                
                except Exception as e : # we can add logging logic here
                    print(e)
                    raise e
                
class CourseSelectionSendAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    def post(self, request, *args, **kwargs) :
        student=Student.objects.get(id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, student)
        term=Term.objects.all().last()
        registeration_request = RegistrationRequest.objects.filter(term=term, student=student).first()
        if registeration_request.confirmation_status == 'not send' :
            registeration_request.confirmation_status = 'waiting'
            registeration_request.save()
        elif registeration_request.confirmation_status == 'waiting' :
            raise PermissionDenied(f"Your are unable to change the confirmation status to waiting twice")
        else :
            raise PermissionDenied(f"Your are unable to change the {registeration_request.confirmation_status} confirmation status to waiting")
        
        return Response({"success": True}, status=200)
    

class CourseSelectionStudentFormsAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameProfessor]
    
    def get(self, request, *args, **kwargs) :
        pk = self.kwargs.get('pk')
        professor = Professor.objects.get(id=pk)
        self.check_object_permissions(self.request, professor)
        students = professor.student_set.all()
        registeration_requests = []
        for student in students :
            registeration_request = RegistrationRequest.objects.filter(term=Term.objects.all().last(), student=student).first()
            serializer = CourseSelectionSerializer(registeration_request)
            registeration_requests.append(serializer.data)

        return Response({"success": True, "registeration_requests" : registeration_requests }, status=200)


class CourseSelectionStudentFormsDetailAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameProfessor]
    
    def get(self, request, *args, **kwargs) :
        pk = self.kwargs.get('pk')
        s_pk = self.kwargs.get('s_pk')
        student = Student.objects.get(id=s_pk)
        professor = Professor.objects.get(id=pk)
        self.check_object_permissions(self.request, professor)
        students = professor.student_set.all()
        if student in students :
            registeration_request = RegistrationRequest.objects.filter(term=Term.objects.all().last(), student=student).first()
            serializer = CourseSelectionSerializer(registeration_request)
            return Response({"success": True, "registeration_request" : serializer.data }, status=200)
        else :
            raise PermissionDenied("You are not allowed to see this student's registeration request.")
        
    def post(self, request, *args, **kwargs) :
        pk = self.kwargs.get('pk')
        s_pk = self.kwargs.get('s_pk')
        student = Student.objects.get(id=s_pk)
        professor = Professor.objects.get(id=pk)
        self.check_object_permissions(self.request, professor)
        students = professor.student_set.all()
        
        if student in students :
            registeration_request = RegistrationRequest.objects.filter(term=Term.objects.all().last(), student=student).first()
            
            if request.data['status'] == 'confirmed' : # we should use celery here to send an email to the student
                registeration_request.confirmation_status = 'confirmed'
                registeration_request.save()
                for course in registeration_request.courses.all() :
                    coursestudent = CourseStudent.objects.create(student=student, course=course, course_status='active', term_taken=Term.objects.all().last())
                    student.courses.add(coursestudent)
                return Response({"success": True, "detail": "confirmed seccessfully"}, status=200)

            elif request.data['status'] == 'failed' :
                registeration_request.confirmation_status = 'not send'
                registeration_request.save()
                return Response({"success": True, "detail": "failed seccessfully"}, status=200)

        
        else :
            raise PermissionDenied("You are not allowed to see this student's registeration request.")
        


class CourseSubstitutionCreationFormAPIView(generics.CreateAPIView) :
    serializer_class = CourseSubstitutionSerializer
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    def post(self, request, *args, **kwargs): # checking creation again
        student_id = self.kwargs.get('pk')
        student = Student.objects.get(id=student_id)
        self.check_object_permissions(self.request, student)
        term = Term.objects.all().last()
        if RemovalAndExtensionRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You have already registered for this course substitution.")
        elif not RegistrationRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You have not registered for this term.")

        return super().post(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        data = {"student": self.kwargs.get('pk'), "term": Term.objects.all().last().id}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    
class CourseSubstitutionListAPIView(generics.ListAPIView) :
    serializer_class = CourseSubstitutionSerializer
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    def get_queryset(self):
        student_id = self.kwargs.get('pk')
        student = Student.objects.get(id=student_id)
        self.check_object_permissions(self.request, student)
        term = Term.objects.all().last()
        return RemovalAndExtensionRequest.objects.filter(term=term, student=student)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        if len(serializer.data) == 0 :
            raise PermissionDenied("You have not registered for course substitution.")
        else :
            data = serializer.data[0]
            response_data = {'status': data['confirmation_status'], 'extended_courses': data['extended_courses'], 'removed_courses': data['removed_courses']}
            return Response(response_data)
        

class CourseSubstitutionCheckAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameStudent]
    

    def post(self, request, *args, **kwargs):
        student=Student.objects.get(id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, student)
        term=Term.objects.all().last()
        RemovalAndExtension_request = RemovalAndExtensionRequest.objects.filter(term=term, student=student).first()
        
        if not RemovalAndExtensionRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You have not registered for course substitution.")
        elif RemovalAndExtension_request.confirmation_status == 'confirmed' :
            raise PermissionDenied("Your registration request confirmed. You can not change it again.") 
        elif RemovalAndExtension_request.confirmation_status == 'Waiting' :
            raise PermissionDenied("You have already sended your registration request. Please wait for confirmation.")
        
        
        # counting units and date_time of selected courses in the database
        units = 0 # 5th validation
        date_and_times = {} # 6th validation
        exams_time = []
        for course in RegistrationRequest.objects.filter(term=term, student=student).first().courses.all() : 
            units += course.name.units
            
            for time in course.class_days_and_times :
                day = time['day']
                if day in date_and_times :
                    date_and_times[day].append((time['start_time'], time['end_time']))
                else :
                    date_and_times[day] = [(time['start_time'], time['end_time'])]
                    
            start = datetime(course.exam_time.year, course.exam_time.month, course.exam_time.day, course.exam_time.hour, course.exam_time.minute)
            end = start + timedelta(hours=2)
            exams_time.append((start, end))
          
            
        added_units = 0
        added_courses = 0
        for course in RemovalAndExtensionRequest.objects.filter(term=term, student=student).first().extended_courses.all() :
            added_units += course.name.units
            added_courses += 1
            
            for time in course.class_days_and_times :
                day = time['day']
                if day in date_and_times :
                    date_and_times[day].append((time['start_time'], time['end_time']))
                else :
                    date_and_times[day] = [(time['start_time'], time['end_time'])]
            
            start = datetime(course.exam_time.year, course.exam_time.month, course.exam_time.day, course.exam_time.hour, course.exam_time.minute)
            end = start + timedelta(hours=2)
            exams_time.append((start, end))
                    
        
            
        deleted_units = 0
        deleted_courses = 0
        for course in RemovalAndExtensionRequest.objects.filter(term=term, student=student).first().removed_courses.all() :
            deleted_units += course.name.units
            deleted_courses += 1
            
            for time in course.class_days_and_times :
                day = time['day']
                date_and_times[day].remove((time['start_time'], time['end_time']))
                    
            start = datetime(course.exam_time.year, course.exam_time.month, course.exam_time.day, course.exam_time.hour, course.exam_time.minute)
            end = start + timedelta(hours=2)
            exams_time.remove((start, end))        
                    
        
        units = units + (added_units - deleted_units)    
            
        if student.intrance_term == term :  # term avali
            
            for pk in request.data['course'] : # counting units of selected courses in the request
                data =  {'course' : [pk] ,'option': request.data['option']}
                serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                serializer.is_valid(raise_exception=True)
                termcourse = TermCourse.objects.get(id=pk)
                if data['option'] == 'add' :
                    units += termcourse.name.units
                    added_units += termcourse.name.units
                    added_courses += 1
                    if units >= 20 :
                        raise serializers.ValidationError("You can not select more than 20 units.")
                    elif added_units >= 6 :
                        raise serializers.ValidationError("You can not add more than 6 units.")
                    elif added_courses >= 2 :
                        raise serializers.ValidationError("You can not add more than 2 courses.")
                    elif termcourse.course_capacity == 0 :
                            raise serializers.ValidationError("The selected course is full.")
                    
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
                        
                    
                    start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                    end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                    for exam_time in exams_time :
                        start = exam_time[0]
                        end = exam_time[1]
                        if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                            raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                    exams_time.append((start_added_exam_time, end_added_exam_time))
                    
                elif data['option'] == 'delete' :
                    units -= termcourse.name.units
                    deleted_units += termcourse.name.units
                    deleted_courses += 1
                    if deleted_units >= 6 :
                        raise serializers.ValidationError("You can not delete more than 6 units.")
                    elif deleted_courses >= 2 :
                        raise serializers.ValidationError("You can not delete more than 2 courses.")
                    
                    for time in termcourse.class_days_and_times :
                        day = time['day']
                        date_and_times[day].remove((time['start_time'], time['end_time']))
                    
                    start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                    end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                    for exam_time in exams_time :
                        start = exam_time[0]
                        end = exam_time[1]
                        exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))

            
            return Response({"success": True}, status=200)
                 
                    
        else :
            secondlast_term = Term.objects.all().reverse()[1]
            if student.term_score(secondlast_term) >= 17 :
                
                for pk in request.data['course'] : # counting units of selected courses in the request
                    data =  {'course' : [pk] ,'option': request.data['option']}
                    serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                    serializer.is_valid(raise_exception=True)
                    termcourse = TermCourse.objects.get(id=pk)
                    if data['option'] == 'add' :
                        units += termcourse.name.units
                        added_units += termcourse.name.units
                        added_courses += 1
                        if units >= 24 :
                            raise serializers.ValidationError("You can not select more than 24 units.")
                        elif added_units >= 6 :
                            raise serializers.ValidationError("You can not add more than 6 units.")
                        elif added_courses >= 2 :
                            raise serializers.ValidationError("You can not add more than 2 courses.")
                        elif termcourse.course_capacity == 0 :
                            raise serializers.ValidationError("The selected course is full.")
                        
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
                            
                        
                        start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                        exams_time.append((start_added_exam_time, end_added_exam_time))
                    
                    elif data['option'] == 'delete' :
                        units -= termcourse.name.units
                        deleted_units += termcourse.name.units
                        deleted_courses += 1
                        if deleted_units >= 6 :
                            raise serializers.ValidationError("You can not delete more than 6 units.")
                        elif deleted_courses >= 2 :
                            raise serializers.ValidationError("You can not delete more than 2 courses.")
                        
                        for time in termcourse.class_days_and_times :
                            day = time['day']
                            date_and_times[day].remove((time['start_time'], time['end_time']))
                        
                        start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
   
                
                
                return Response({"success": True}, status=200)
            
            else :
                for pk in request.data['course'] : # counting units of selected courses in the request
                    data =  {'course' : [pk] ,'option': request.data['option']}
                    serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                    serializer.is_valid(raise_exception=True)
                    termcourse = TermCourse.objects.get(id=pk)
                    if data['option'] == 'add' :
                        units += termcourse.name.units
                        added_units += termcourse.name.units
                        added_courses += 1
                        if units >= 20 :
                            raise serializers.ValidationError("You can not select more than 20 units.")
                        elif added_units >= 6 :
                            raise serializers.ValidationError("You can not add more than 6 units.")
                        elif added_courses >= 2 :
                            raise serializers.ValidationError("You can not add more than 2 courses.")
                        elif termcourse.course_capacity == 0 :
                            raise serializers.ValidationError("The selected course is full.")
                        
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
                            
                        
                        start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                        exams_time.append((start_added_exam_time, end_added_exam_time))
                        
                    elif data['option'] == 'delete' :
                        units -= termcourse.name.units
                        deleted_units += termcourse.name.units
                        deleted_courses += 1
                        if deleted_units >= 6 :
                            raise serializers.ValidationError("You can not delete more than 6 units.")
                        elif deleted_courses >= 2 :
                            raise serializers.ValidationError("You can not delete more than 2 courses.")
                        
                        for time in termcourse.class_days_and_times :
                            day = time['day']
                            date_and_times[day].remove((time['start_time'], time['end_time']))
                        
                        start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
                
                return Response({"success": True}, status=200)
            

            
class CourseSubstitutionSubmitAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        student=Student.objects.get(id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, student)
        term=Term.objects.all().last()
        RemovalAndExtension_request = RemovalAndExtensionRequest.objects.filter(term=term, student=student).first()
        registeration_request = RegistrationRequest.objects.filter(term=term, student=student).first()
        
        if not RemovalAndExtensionRequest.objects.filter(term=term, student=student).exists() :
            raise PermissionDenied("You have not registered for course substitution.")
        elif RemovalAndExtension_request.confirmation_status == 'confirmed' :
            raise PermissionDenied("Your registration request confirmed. You can not change it again.") 
        elif RemovalAndExtension_request.confirmation_status == 'Waiting' :
            raise PermissionDenied("You have already sended your registration request. Please wait for confirmation.")
        
        
        # counting units and date_time of selected courses in the database
        units = 0 # 5th validation
        date_and_times = {} # 6th validation
        exams_time = []
        for course in RegistrationRequest.objects.filter(term=term, student=student).first().courses.all() : 
            units += course.name.units
            
            for time in course.class_days_and_times :
                day = time['day']
                if day in date_and_times :
                    date_and_times[day].append((time['start_time'], time['end_time']))
                else :
                    date_and_times[day] = [(time['start_time'], time['end_time'])]
                    
            start = datetime(course.exam_time.year, course.exam_time.month, course.exam_time.day, course.exam_time.hour, course.exam_time.minute)
            end = start + timedelta(hours=2)
            exams_time.append((start, end))
          
            
        added_units = 0
        added_courses = 0
        for course in RemovalAndExtensionRequest.objects.filter(term=term, student=student).first().extended_courses.all() :
            added_units += course.name.units
            added_courses += 1
            
            for time in course.class_days_and_times :
                day = time['day']
                if day in date_and_times :
                    date_and_times[day].append((time['start_time'], time['end_time']))
                else :
                    date_and_times[day] = [(time['start_time'], time['end_time'])]
            
            start = datetime(course.exam_time.year, course.exam_time.month, course.exam_time.day, course.exam_time.hour, course.exam_time.minute)
            end = start + timedelta(hours=2)
            exams_time.append((start, end))
                    
        
            
        deleted_units = 0
        deleted_courses = 0
        for course in RemovalAndExtensionRequest.objects.filter(term=term, student=student).first().removed_courses.all() :
            deleted_units += course.name.units
            deleted_courses += 1
            
            for time in course.class_days_and_times :
                day = time['day']
                date_and_times[day].remove((time['start_time'], time['end_time']))
                    
            start = datetime(course.exam_time.year, course.exam_time.month, course.exam_time.day, course.exam_time.hour, course.exam_time.minute)
            end = start + timedelta(hours=2)
            exams_time.remove((start, end))        
                    
        
        units = units + (added_units - deleted_units)    
            
        if student.intrance_term == term :  # term avali
            try :
                for pk in request.data['course'] : # counting units of selected courses in the request
                    data =  {'course' : [pk] ,'option': request.data['option']}
                    serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                    serializer.is_valid(raise_exception=True)
                    termcourse = TermCourse.objects.get(id=pk)
                    if data['option'] == 'add' :
                        units += termcourse.name.units
                        added_units += termcourse.name.units
                        added_courses += 1
                        if units >= 20 :
                            raise serializers.ValidationError("You can not select more than 20 units.")
                        elif added_units >= 6 :
                            raise serializers.ValidationError("You can not add more than 6 units.")
                        elif added_courses >= 2 :
                            raise serializers.ValidationError("You can not add more than 2 courses.")
                        elif termcourse.course_capacity == 0 :
                                raise serializers.ValidationError("The selected course is full.")
                        
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
                            
                        
                        start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                        for exam_time in exams_time :
                            start = exam_time[0]
                            end = exam_time[1]
                            if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                        exams_time.append((start_added_exam_time, end_added_exam_time))
                        
                        termcourse.course_capacity -= 1
                        termcourse.save()
                        if termcourse in RemovalAndExtension_request.removed_courses.all() and termcourse in registeration_request.courses.all() :
                            RemovalAndExtension_request.removed_courses.remove(termcourse)
                        else :
                            RemovalAndExtension_request.extended_courses.add(termcourse)
                        
                    
                    elif data['option'] == 'delete' :
                        units -= termcourse.name.units
                        deleted_units += termcourse.name.units
                        deleted_courses += 1
                        if deleted_units >= 6 :
                            raise serializers.ValidationError("You can not delete more than 6 units.")
                        elif deleted_courses >= 2 :
                            raise serializers.ValidationError("You can not delete more than 2 courses.")
                        
                        for time in termcourse.class_days_and_times :
                            day = time['day']
                            date_and_times[day].remove((time['start_time'], time['end_time']))
                        
                        start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                        end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                        exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
                        
                        termcourse.course_capacity += 1
                        termcourse.save()
                        if termcourse in RemovalAndExtension_request.extended_courses.all() :
                            RemovalAndExtension_request.extended_courses.remove(termcourse)
                        else :
                            RemovalAndExtension_request.removed_courses.add(termcourse)
                        
            except Exception as e :
                print(e)
                raise e

            
            return Response({"success": True}, status=200)
                 
                    
        else :
            secondlast_term = Term.objects.all().reverse()[1]
            if student.term_score(secondlast_term) >= 17 :
                try :
                    for pk in request.data['course'] : # counting units of selected courses in the request
                        data =  {'course' : [pk] ,'option': request.data['option']}
                        serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                        serializer.is_valid(raise_exception=True)
                        termcourse = TermCourse.objects.get(id=pk)
                        if data['option'] == 'add' :
                            units += termcourse.name.units
                            added_units += termcourse.name.units
                            added_courses += 1
                            if units >= 24 :
                                raise serializers.ValidationError("You can not select more than 24 units.")
                            elif added_units >= 6 :
                                raise serializers.ValidationError("You can not add more than 6 units.")
                            elif added_courses >= 2 :
                                raise serializers.ValidationError("You can not add more than 2 courses.")
                            elif termcourse.course_capacity == 0 :
                                raise serializers.ValidationError("The selected course is full.")
                            
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
                                
                            
                            start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                            end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                            for exam_time in exams_time :
                                start = exam_time[0]
                                end = exam_time[1]
                                if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                    raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                            exams_time.append((start_added_exam_time, end_added_exam_time))
                            
                            termcourse.course_capacity -= 1
                            termcourse.save()
                            if termcourse in RemovalAndExtension_request.removed_courses.all() and termcourse in registeration_request.courses.all() :
                                RemovalAndExtension_request.removed_courses.remove(termcourse)
                            else :
                                RemovalAndExtension_request.extended_courses.add(termcourse)
                        
                        
                        elif data['option'] == 'delete' :
                            units -= termcourse.name.units
                            deleted_units += termcourse.name.units
                            deleted_courses += 1
                            if deleted_units >= 6 :
                                raise serializers.ValidationError("You can not delete more than 6 units.")
                            elif deleted_courses >= 2 :
                                raise serializers.ValidationError("You can not delete more than 2 courses.")
                            
                            for time in termcourse.class_days_and_times :
                                day = time['day']
                                date_and_times[day].remove((time['start_time'], time['end_time']))
                            
                            start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                            end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                            for exam_time in exams_time :
                                start = exam_time[0]
                                end = exam_time[1]
                                exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
                                
                            termcourse.course_capacity += 1
                            termcourse.save()
                            if termcourse in RemovalAndExtension_request.extended_courses.all() :
                                RemovalAndExtension_request.extended_courses.remove(termcourse)
                            else :
                                RemovalAndExtension_request.removed_courses.add(termcourse)
   
                except Exception as e :
                    print(e)
                    raise e
                
                return Response({"success": True}, status=200)
            
            else :
                try :
                    for pk in request.data['course'] : # counting units of selected courses in the request
                        data =  {'course' : [pk] ,'option': request.data['option']}
                        serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
                        serializer.is_valid(raise_exception=True)
                        termcourse = TermCourse.objects.get(id=pk)
                        if data['option'] == 'add' :
                            units += termcourse.name.units
                            added_units += termcourse.name.units
                            added_courses += 1
                            if units >= 20 :
                                raise serializers.ValidationError("You can not select more than 20 units.")
                            elif added_units >= 6 :
                                raise serializers.ValidationError("You can not add more than 6 units.")
                            elif added_courses >= 2 :
                                raise serializers.ValidationError("You can not add more than 2 courses.")
                            elif termcourse.course_capacity == 0 :
                                raise serializers.ValidationError("The selected course is full.")
                            
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
                                
                            
                            start_added_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                            end_added_exam_time = start_added_exam_time + timedelta(hours=2)
                            for exam_time in exams_time :
                                start = exam_time[0]
                                end = exam_time[1]
                                if (start_added_exam_time < end and start_added_exam_time > start) or (end_added_exam_time > start and end_added_exam_time < end) :
                                    raise serializers.ValidationError(f"the selected { termcourse } course's exam time interferes with previous courses")
                            exams_time.append((start_added_exam_time, end_added_exam_time))
                            
                            termcourse.course_capacity -= 1
                            termcourse.save()
                            if termcourse in RemovalAndExtension_request.removed_courses.all() and termcourse in registeration_request.courses.all() :
                                RemovalAndExtension_request.removed_courses.remove(termcourse)
                            else :
                                RemovalAndExtension_request.extended_courses.add(termcourse)
                            
                        elif data['option'] == 'delete' :
                            units -= termcourse.name.units
                            deleted_units += termcourse.name.units
                            deleted_courses += 1
                            if deleted_units >= 6 :
                                raise serializers.ValidationError("You can not delete more than 6 units.")
                            elif deleted_courses >= 2 :
                                raise serializers.ValidationError("You can not delete more than 2 courses.")
                            
                            for time in termcourse.class_days_and_times :
                                day = time['day']
                                date_and_times[day].remove((time['start_time'], time['end_time']))
                            
                            start_deleted_exam_time = datetime(termcourse.exam_time.year, termcourse.exam_time.month, termcourse.exam_time.day, termcourse.exam_time.hour, termcourse.exam_time.minute)
                            end_deleted_exam_time = start_deleted_exam_time + timedelta(hours=2)
                            for exam_time in exams_time :
                                start = exam_time[0]
                                end = exam_time[1]
                                exams_time.remove((start_deleted_exam_time, end_deleted_exam_time))
                            
                            termcourse.course_capacity += 1
                            termcourse.save()
                            if termcourse in RemovalAndExtension_request.extended_courses.all() :
                                RemovalAndExtension_request.extended_courses.remove(termcourse)
                            else :
                                RemovalAndExtension_request.removed_courses.add(termcourse)
                                
                                
                except Exception as e :
                    print(e)
                    raise e
                
                return Response({"success": True}, status=200)
            
class CourseSubstitutionSendAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameStudent]
    
    def post(self, request, *args, **kwargs) :
        student=Student.objects.get(id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, student)
        term=Term.objects.all().last()
        registeration_request = RemovalAndExtensionRequest.objects.filter(term=term, student=student).first()
        if registeration_request.confirmation_status == 'not send' :
            registeration_request.confirmation_status = 'waiting'
            registeration_request.save()
        elif registeration_request.confirmation_status == 'Waiting' :
            raise PermissionDenied(f"Your are unable to change the confirmation status to waiting twice")
        else :
            raise PermissionDenied(f"Your are unable to change the {registeration_request.confirmation_status} confirmation status to waiting")
        
        return Response({"success": True}, status=200)
    
    
class CourseSubstitutionStudentFormsAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameProfessor]
    
    def get(self, request, *args, **kwargs) :
        pk = self.kwargs.get('pk')
        professor = Professor.objects.get(id=pk)
        self.check_object_permissions(self.request, professor)
        students = professor.student_set.all()
        registeration_requests = []
        for student in students :
            registeration_request = RemovalAndExtensionRequest.objects.filter(term=Term.objects.all().last(), student=student).first()
            serializer = CourseSubstitutionSerializer(registeration_request)
            registeration_requests.append(serializer.data)

        return Response({"success": True, "substitution_requests" : registeration_requests }, status=200)



class CourseSubstitutionStudentFormsDetailAPIView(views.APIView) :
    permission_classes = [IsAuthenticated, IsSameProfessor]
    
    def get(self, request, *args, **kwargs) :
        pk = self.kwargs.get('pk')
        s_pk = self.kwargs.get('s_pk')
        student = Student.objects.get(id=s_pk)
        professor = Professor.objects.get(id=pk)
        self.check_object_permissions(self.request, professor)
        students = professor.student_set.all()
        if student in students :
            registeration_request = RemovalAndExtensionRequest.objects.filter(term=Term.objects.all().last(), student=student).first()
            serializer = CourseSubstitutionSerializer(registeration_request)
            return Response({"success": True, "substitution_request" : serializer.data }, status=200)
        else :
            raise PermissionDenied("You are not allowed to see this student's substitution request.")
        
        
    def post(self, request, *args, **kwargs) :
        pk = self.kwargs.get('pk')
        s_pk = self.kwargs.get('s_pk')
        student = Student.objects.get(id=s_pk)
        professor = Professor.objects.get(id=pk)
        self.check_object_permissions(self.request, professor)
        students = professor.student_set.all()
        
        if student in students :
            registeration_request = RemovalAndExtensionRequest.objects.filter(term=Term.objects.all().last(), student=student).first()
            
            if request.data['status'] == 'confirmed' : # we should use celery here to send an email to the student
                registeration_request.confirmation_status = 'Confirmed'
                registeration_request.save()
                for course in registeration_request.extended_courses.all() :
                    coursestudent = CourseStudent.objects.create(student=student, course=course, course_status='active', term_taken=Term.objects.all().last())
                    student.courses.add(coursestudent)
                    
                for course in registeration_request.removed_courses.all() :
                    coursestudent = CourseStudent.objects.get(student=student, course=course, course_status='active', term_taken=Term.objects.all().last())
                    coursestudent.course_status = 'deleted'
                    coursestudent.save()
                    student.courses.remove(coursestudent)
                    
                return Response({"success": True, "detail": "confirmed seccessfully"}, status=200)

            elif request.data['status'] == 'failed' :
                registeration_request.confirmation_status = 'Not Send'
                registeration_request.save()
                return Response({"success": True, "detail": "failed seccessfully"}, status=200)

        
        else :
            raise PermissionDenied("You are not allowed to see this student's substitution request.")
    

class ReconsiderationRequestStudentView(APIView):
    # permission_classes = [IsAuthenticated, IsSameStudent]
    serializer_class = InputReconsiderationStudentSerializer

    def get_serializer_class(self):
        if self.request.method == "POST" or self.request.method == "PUT":
            return OutputReconsiderationStudentSerializer
        else :
            return InputReconsiderationStudentSerializer


    def post(self, request, std_id, co_id):
        serializer = InputReconsiderationStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = CourseStudent.objects.get(id=co_id)
        student = Student.objects.get(id=std_id)
        if ReconsiderationRequest.objects.filter(student=student, course=course).exists():
            return Response(
            "Reconsideration request exists.",
            status=status.HTTP_400_BAD_REQUEST)
        try:
            query = ReconsiderationRequest.objects.create(
                course=course,
                student=student,
                reconsideration_text=serializer.validated_data.get("reconsideration_text"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        return Response(OutputReconsiderationStudentSerializer(query, context={"request":request}).data)

    def get(self, request, std_id, co_id):
        student = Student.objects.get(id=std_id)
        course = CourseStudent.objects.get(id=co_id)
        if student is None:
            return Response(
                "Student not found with given id.",
                status=status.HTTP_400_BAD_REQUEST)
        if course is None:
            return Response(
                "Course not found with given id.",
                status=status.HTTP_400_BAD_REQUEST)
        try:
            query = ReconsiderationRequest.objects.get(student=student, course=course)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(OutputReconsiderationStudentSerializer(query, context={"request":request}).data)

    def put(self, request, std_id, co_id):
        serializer = InputReconsiderationStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = Student.objects.get(id=std_id)
        course = CourseStudent.objects.get(id=co_id)
        if student is None:
            return Response(
                "Student not found with given id.",
                status=status.HTTP_400_BAD_REQUEST)
        if course is None:
            return Response(
                "Course not found with given id.",
                status=status.HTTP_400_BAD_REQUEST)
        try:
            query = ReconsiderationRequest.objects.update(
                reconsideration_text=serializer.validated_data.get("reconsideration_text"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(OutputReconsiderationStudentSerializer(query, context={"request":request}).data)

    
    def delete(self, request, std_id, co_id):
        student = Student.objects.get(id=std_id)
        course = CourseStudent.objects.get(id=co_id)
        if student is None:
            return Response(
                "Student not found with given id.",
                status=status.HTTP_400_BAD_REQUEST)
        if course is None:
            return Response(
                "Course not found with given id.",
                status=status.HTTP_400_BAD_REQUEST)
        try:
            query = ReconsiderationRequest.objects.delete(student=student, course=course)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(OutputReconsiderationStudentSerializer(query, context={"request":request}).data)



class ReconsiderationRequestProfessorView(APIView):
    # permission_classes = [IsAuthenticated, IsSameProfessor]
    serializer_class = InputReconsiderationProfessorSerializer

    def get_serializer_class(self):
        if self.request.method == "PUT":
            return OutputReconsiderationProfessorSerializer
        else :
            return InputReconsiderationProfessorSerializer


    def put(self, request, std_id, co_id):
        serializer = InputReconsiderationProfessorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = CourseStudent.objects.get(id=co_id)
        student = Student.objects.get(id=std_id)
        if not ReconsiderationRequest.objects.filter(student=student, course=course).exists():
            return Response(
            "Reconsideration request dose not exist.",
            status=status.HTTP_400_BAD_REQUEST)
        try:
            CourseStudent.objects.update(student_score=serializer.validated_data.get("new_grade"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        try:
            query = ReconsiderationRequest.objects.update(
                course=course,
                student=student,
                reconsideration_response=serializer.validated_data.get("reconsideration_response"))
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        return Response(OutputReconsiderationProfessorSerializer(query, context={"request":request}).data)

    def get(self, request, std_id, co_id):
        student = Student.objects.get(id=std_id)
        course = CourseStudent.objects.get(id=co_id)
        if student is None:
            return Response(
                "Student not found with given id.",
                status=status.HTTP_400_BAD_REQUEST)
        if course is None:
            return Response(
                "Course not found with given id.",
                status=status.HTTP_400_BAD_REQUEST)
        try:
            query = ReconsiderationRequest.objects.get(student=student, course=course)
        except Exception as ex:
            return Response(
                f"Database Error {ex}",
                status=status.HTTP_400_BAD_REQUEST)
        
        return Response(OutputReconsiderationProfessorSerializer(query, context={"request":request}).data)



class TermsListView(APIView):

    permission_classes = [
        permissions.IsAuthenticated,
        (IsSameStudent | IsSameProfessor),
    ]

    def get(self, request):
        queryset = Term.objects.all()
        self.check_permissions(request, queryset)
        ser_data = TermSerializer(instance=queryset, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class TermsDetailView(APIView):

    permission_classes = [
        permissions.IsAuthenticated,
        (IsSameStudent | IsSameProfessor),
    ]

    def get(self, request, pk):
        queryset = Term.objects.get(pk=pk)
        self.check_object_permissions(request, queryset)
        ser_data = TermSerializer(instance=queryset, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentApprovedCourseView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsSameStudent,
    ]

    def get(self, request, pk):
        student = Student.objects.get(pk=pk)
        self.check_object_permissions(request, student)
        course_list = CourseStudent.objects.filter(student=student)
        course_list.exclude(course_status__in=['active', 'passed'])
        course_list.filter(Q(
            course__pre_requisites__in=student.passed_courses) | Q(
            course__co_requisites__in=student.passed_courses)).distinct()
        ser_data = CourseStudentSerializer(instance=course_list, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentPassedCourseView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsITManagerOrEducationalAssistantWithSameFaculty | IsSameStudent | IsSupervisor,
    ]

    def get(self, request, pk):
        student = Student.objects.get(pk=pk)
        self.check_object_permissions(request, student)
        course = CourseStudent.objects.exclude(course_status='active')
        course.exclude(course_status='deleted')
        ser_data = CourseStudentSerializer(instance=course, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentTermCourseView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsITManagerOrEducationalAssistantWithSameFaculty | IsSupervisor,
    ]

    def get(self, request, pk):
        student = Student.objects.get(pk=pk)
        self.check_object_permissions(request, student)
        course = CourseStudent.objects.filter(course_status='active')
        ser_data = CourseStudentSerializer(instance=course, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentRemainedTermView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsSameStudent,
    ]

    def get(self, request, pk):
        student = Student.objects.get(pk=pk)
        self.check_object_permissions(request, student)
        ser_data = StudentSerializer(instance=student, many=True)
        if ser_data.is_valid():
            remaining_years = 5 - student.years

            if remaining_years < 0:
                remaining_years = 0

            response_data = {
                "remaining_years": remaining_years,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class EmergencyRemoveRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudentForRemoval]

    def post(self, request, *args, **kwargs):
        ser_data = EmergencyRemoveSerializer(data=request.data, many=True)
        self.check_object_permissions(request, ser_data.data)
        if ser_data.is_valid():
            ser_data.save()
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, s_pk, c_pk):
        student = Student.objects.get(pk=s_pk)
        course = TermCourse.objects.get(pk=c_pk)
        removal_request = EmergencyRemovalRequest.objects.filter(
            student=student, course=course).first()
        ser_data = EmergencyRemoveSerializer(instance=removal_request)
        self.check_object_permissions(request, ser_data.data)
        return Response(ser_data.data, status=status.HTTP_200_OK)

    def put(self, request, s_pk, c_pk):
        student = Student.objects.get(pk=s_pk)
        course = TermCourse.objects.get(pk=c_pk)
        removal_request = EmergencyRemovalRequest.objects.filter(
            student=student, course=course).first()
        ser_data = EmergencyRemoveSerializer(
            instance=removal_request, data=request.data, partial=True)
        self.check_object_permissions(request, ser_data.data)
        if ser_data.is_valid():
            ser_data.save()
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, s_pk, c_pk):
        student = Student.objects.get(pk=s_pk)
        course = TermCourse.objects.get(pk=c_pk)
        removal_request = EmergencyRemovalRequest.objects.filter(
            student=student, course=course).first()
        self.check_object_permissions(request, removal_request)
        removal_request.delete()
        return Response({'message': "request deleted"}, status=status.HTTP_200_OK)


class CourseRemovalListView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsITManagerOrEducationalAssistantWithSameFaculty,
        ]

    def get(self, request, pk):
        edu_assistant = EducationalAssistant.objects.get(pk=pk)
        queryset = EmergencyRemovalRequest.objects.all()
        self.check_permissions(request, edu_assistant)
        ser_data = EmergencyRemoveSerializer(instance=queryset, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseRemovalDetailView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsITManagerOrEducationalAssistantWithSameFaculty,
        ]

    def get(self, request, a_pk, e_pk):
        edu_assistant = EducationalAssistant.objects.get(pk=a_pk)
        queryset = EmergencyRemovalRequest.objects.get(pk=e_pk)
        self.check_permissions(request, edu_assistant)
        ser_data = EmergencyRemoveSerializer(instance=queryset, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        ser_data = EmergencyRemoveSerializer(data=request.data, many=True)
        self.check_object_permissions(request, ser_data.data)
        if ser_data.is_valid():
            ser_data.save()
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class TermRemoveRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudentForRemoval]

    def post(self, request, *args, **kwargs):
        ser_data = TermRemoveSerializer(data=request.data, many=True)
        self.check_object_permissions(request, ser_data.data)
        if ser_data.is_valid():
            ser_data.save()
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, s_pk, t_pk):
        student = Student.objects.get(pk=s_pk)
        course = Term.objects.get(pk=t_pk)
        removal_request = TermRemovalRequest.objects.filter(
            student=student, course=course).first()
        ser_data = TermRemoveSerializer(instance=removal_request)
        self.check_object_permissions(request, ser_data.data)
        return Response(ser_data.data, status=status.HTTP_200_OK)

    def put(self, request, s_pk, c_pk):
        student = Student.objects.get(pk=s_pk)
        course = Term.objects.get(pk=c_pk)
        removal_request = TermRemovalRequest.objects.filter(
            student=student, course=course).first()
        ser_data = TermRemoveSerializer(
            instance=removal_request, data=request.data, partial=True)
        self.check_object_permissions(request, ser_data.data)
        if ser_data.is_valid():
            ser_data.save()
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, s_pk, c_pk):
        student = Student.objects.get(pk=s_pk)
        course = Term.objects.get(pk=c_pk)
        removal_request = TermRemovalRequest.objects.filter(
            student=student, course=course).first()
        self.check_object_permissions(request, removal_request)
        removal_request.delete()
        return Response({'message': "request deleted"}, status=status.HTTP_200_OK)


class TermRemovalListView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsITManagerOrEducationalAssistantWithSameFaculty,
        ]

    def get(self, request, pk):
        edu_assistant = EducationalAssistant.objects.get(pk=pk)
        queryset = TermRemovalRequest.objects.all()
        self.check_permissions(request, edu_assistant)
        ser_data = TermRemoveSerializer(instance=queryset, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)


class TermRemovalDetailView(APIView):
    permission_classes = [
        permissions.IsAuthenticated,
        IsITManagerOrEducationalAssistantWithSameFaculty,
        ]

    def get(self, request, a_pk, e_pk):
        edu_assistant = EducationalAssistant.objects.get(pk=a_pk)
        queryset = TermRemovalRequest.objects.get(pk=e_pk)
        self.check_permissions(request, edu_assistant)
        ser_data = TermRemoveSerializer(instance=queryset, many=True)
        if ser_data.is_valid():
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        ser_data = EmergencyRemoveSerializer(data=request.data, many=True)
        self.check_object_permissions(request, ser_data.data)
        if ser_data.is_valid():
            ser_data.save()
            return Response(ser_data.data, status=status.HTTP_200_OK)

        return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)
