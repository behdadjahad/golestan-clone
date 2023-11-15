from rest_framework import serializers
from faculty.models import ApprovedCourse, Faculty


class FacultySerializer(serializers.ModelSerializer) :
    class Meta :
        model = Faculty
        fields = [
            "id",
            "name",
        ]
    # def create(self, validated_data):
    #     return Faculty.objects.create(**validated_data)



class ApprovedCourseSerializer(serializers.ModelSerializer) :
    # faculty_name = serializers.StringRelatedField(source='faculty.name', read_only=True) 
     
    class Meta :
        model = ApprovedCourse
        fields = [
            "id",
            "course_name",
            "faculty",
            "pre_requisites",
            "co_requisites",
            "units",
            "course_type"
        ]
        
    def to_representation(self, instance):
            representation = super().to_representation(instance)
            representation['pre_requisites'] = [course.course_name for course in instance.pre_requisites.all()]
            representation['co_requisites'] = [course.course_name for course in instance.co_requisites.all()]
            return representation  
    
    
