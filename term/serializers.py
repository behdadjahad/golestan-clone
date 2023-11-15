from rest_framework import serializers
from term.models import TermCourse, Term
from datetime import datetime, date

class TermCourseSerializer(serializers.ModelSerializer) :
    # course_name = serializers.StringRelatedField(source='name.course_name', read_only=True)
    # term_name = serializers.StringRelatedField(source='term.term_name', read_only=True)
    # course_professor_name = serializers.StringRelatedField(source='course_professor', read_only=True)

    class Meta :
        model = TermCourse
        fields = [
            "id",
            "name",
            "class_days_and_times",
            "exam_time",
            "exam_place",
            "course_professor",
            "course_capacity",
            "term",
        ]
        
    def validate(self, attrs) :
        term = attrs["term"]
        repairing_unit_selection_end_time = term.repairing_unit_selection_end_time    
        term_end_time = term.term_end_time
        now = datetime.now()
        now = date(now.year, now.month, now.day)
        repairing_unit_selection_end_time = date(repairing_unit_selection_end_time.year, repairing_unit_selection_end_time.month, repairing_unit_selection_end_time.day)
        term_end_time = date(term_end_time.year, term_end_time.month, term_end_time.day)
        if now < term_end_time and now > repairing_unit_selection_end_time:
            raise serializers.ValidationError("Cannot create TermCourse instance. Invalid datetime range.")
        
        course = attrs["name"]
        if course.course_type == "practical" and (attrs.get("exam_time", None) is not None or attrs.get("exam_place", None) is not None):
            raise serializers.ValidationError("Cannot create TermCourse instance. practical courses cannot have exam_time and exam_place.")
        
        
        
        return attrs

        
    