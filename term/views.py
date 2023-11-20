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

from term.serializers import CourseSelectionSerializer, CourseSelectionCheckSerializer, CourseSubstitutionSerializer

from account.models import Professor, Student

from datetime import datetime, timedelta

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
                serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
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
                    
                elif data['course'] == 'delete' :
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
                    serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
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
                        
                    elif data['course'] == 'delete' :
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
                    serializer = CourseSubstitutionCheckSerializer(data=data, context={'pk': self.kwargs.get('pk')})
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
                        
                    elif data['course'] == 'delete' :
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
        if registeration_request.confirmation_status == 'Not Send' :
            registeration_request.confirmation_status = 'waiting'
            registeration_request.save()
        elif registeration_request.confirmation_status == 'Waiting' :
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
                    
                elif data['course'] == 'delete' :
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
                    
                    elif data['course'] == 'delete' :
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
                        
                    elif data['course'] == 'delete' :
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
                        RemovalAndExtension_request.extended_courses.add(termcourse)
            
                    
                    
                    elif data['course'] == 'delete' :
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
                            RemovalAndExtension_request.extended_courses.add(termcourse)
                        
                        elif data['course'] == 'delete' :
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
                            RemovalAndExtension_request.extended_courses.add(termcourse)
                            
                        elif data['course'] == 'delete' :
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
        if registeration_request.confirmation_status == 'Not Send' :
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
                    coursestudent.course_status = 'Deleted'
                    coursestudent.save()
                    student.courses.remove(coursestudent)
                    
                return Response({"success": True, "detail": "confirmed seccessfully"}, status=200)

            elif request.data['status'] == 'failed' :
                registeration_request.confirmation_status = 'Not Send'
                registeration_request.save()
                return Response({"success": True, "detail": "failed seccessfully"}, status=200)

        
        else :
            raise PermissionDenied("You are not allowed to see this student's substitution request.")
    
