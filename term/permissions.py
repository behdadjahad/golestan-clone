from rest_framework.permissions import BasePermission

from account.models import EducationalAssistant, ITManager


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