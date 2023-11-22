from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Term)
admin.site.register(TermCourse)
admin.site.register(CourseStudent)
admin.site.register(RegistrationRequest)
admin.site.register(EnrollmentCertificateRequest)