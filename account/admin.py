from django.contrib import admin
from .models import *


# Register your models here.
admin.site.register(Professor)
# admin.site.register(Student)
admin.site.register(ITManager)
admin.site.register(EducationalAssistant)

class CourseInline(admin.TabularInline):  # or admin.StackedInline
    model = Student.courses.through
    
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    inlines = [CourseInline]

