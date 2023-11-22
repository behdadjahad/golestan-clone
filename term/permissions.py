from rest_framework.permissions import BasePermission

from account.models import EducationalAssistant, ITManager, Professor, Student


class IsITManagerOrEducationalAssistantWithSameFaculty(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if ITManager.objects.filter(username=user.username).exists() or request.method == 'GET':
            return True
        elif EducationalAssistant.objects.filter(username=user.username).exists():
            eda = EducationalAssistant.objects.get(username=user.username)
            if request.method == 'POST' :
                return obj == eda.faculty
            
            elif request.method == 'PUT' or request.method == 'DELETE':
                return obj.faculty == eda.faculty
            else :
                return True
        else :
            return False
        
class IsSameStudent(BasePermission):
    def has_permission(self, request, view):
        username = request.user.username
        return request.user.is_authenticated and Student.objects.filter(username=username).exists()
    
    def has_object_permission(self, request, view, obj):
        username = request.user.username
        student = Student.objects.get(username=username)
        return obj == student 
    

class IsSameProfessor(BasePermission):
    def has_permission(self, request, view):
        username = request.user.username
        return request.user.is_authenticated and Professor.objects.filter(username=username).exists()
    
    def has_object_permission(self, request, view, obj):
        username = request.user.username
        professor = Professor.objects.get(username=username)
        return obj == professor 
    
class IsSameEducationalAssistant(BasePermission) :
    def has_permission(self, request, view) :
        username = request.user.username
        return request.user.is_authenticated and EducationalAssistant.objects.filter(username=username).exists()
    
    def has_object_permission(self, request, view, obj) :
        username = request.user.username
        eda = EducationalAssistant.objects.get(username=username)
        return obj == eda