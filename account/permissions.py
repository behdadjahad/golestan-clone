from rest_framework.permissions import BasePermission
from account.models import EducationalAssistant, ITManager, Student, Professor
from user.models import User


class IsStudentOrEducationalAssistant(BasePermission):
    def has_permission(self, request, view):
        SAFE_METHODS = ['GET', 'PUT']
        user = request.user
        indivisual = Student.objects.filter(username=user.username).exists() or EducationalAssistant.objects.filter(username=user.username).exists()
        return request.user.is_authenticated and request.method in SAFE_METHODS and indivisual

    def has_object_permission(self, request, view, obj):
        user = request.user
        if Student.objects.filter(username=user.username).exists() and (request.method == 'GET' or request.method == 'PUT'):
            stu = Student.objects.get(username=user.username)
            return obj == stu
        
        elif EducationalAssistant.objects.filter(username=user.username).exists() and request.method == 'GET':
            eda = EducationalAssistant.objects.get(username=user.username)
            return obj.faculty == eda.faculty
        
        else:
            return False
     
        
class IsProfessorOrEducationalAssistant(BasePermission):
    def has_permission(self, request, view):
        SAFE_METHODS = ['GET', 'PUT']
        user = request.user
        indivisual = Professor.objects.filter(username=user.username).exists() or EducationalAssistant.objects.filter(username=user.username).exists()
        return request.user.is_authenticated and request.method in SAFE_METHODS and indivisual

    def has_object_permission(self, request, view, obj):
        user = request.user
        if Professor.objects.filter(username=user.username).exists() and (request.method == 'GET' or request.method == 'PUT'):
            prof = Professor.objects.get(username=user.username)
            return obj == prof
        
        elif EducationalAssistant.objects.filter(username=user.username).exists() and request.method == 'GET':
            eda = EducationalAssistant.objects.get(username=user.username)
            return obj.faculty == eda.faculty
        
        else:
            return False

class IsItManager(BasePermission):
    def has_permission(self, request, view):
        # SAFE_METHODS = ['GET', 'PUT']
        user = request.user
        indivisual = ITManager.objects.filter(username=user.username).exists()
        return request.user.is_authenticated and indivisual
