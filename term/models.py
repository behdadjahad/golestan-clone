from django.db import models

from account.models import Professor, Student
from faculty.models import ApprovedCourse, Department


# Create your models here.
class Term(models.Model) :
    term_name = models.CharField(max_length=100)
    students_registered = models.ManyToManyField('account.Student', related_name='registered_term_students', blank=True) # add an update
    professor_registered = models.ManyToManyField('account.Professor', related_name='registered_term_professor', blank=True) # add an update
    term_courses = models.ManyToManyField('term.TermCourse', related_name='courses_term', blank=True) # add an update
    unit_selection_start_time = models.DateTimeField()
    unit_selection_end_time = models.DateTimeField()
    courses_start_time = models.DateField()
    courses_end_time = models.DateField()
    repairing_unit_selection_start_time = models.DateTimeField()
    repairing_unit_selection_end_time = models.DateTimeField()
    emergency_deletion_end_time = models.DateTimeField()
    exams_start_time = models.DateField()
    term_end_time = models.DateField()

    def __str__(self):
        return f"{self.term_name}"



class TermCourse(models.Model) :
    name = models.ForeignKey(ApprovedCourse, on_delete=models.PROTECT) # added # its better to be course instead of name
    class_days_and_times = models.JSONField(help_text="Select class days and times in JSON format")
    exam_time = models.DateTimeField(null=True, blank=True)
    exam_place = models.CharField(max_length=100, null=True, blank=True)
    course_professor = models.ForeignKey(Professor, on_delete=models.PROTECT)
    course_capacity = models.PositiveIntegerField()      # add def update?
    term = models.ForeignKey(Term, on_delete=models.PROTECT)
    # departmant = models.ManyToManyField(Department) # added
    
    def __str__(self):
        formatted_days_and_times = [
            f"{day_and_time.get('day')}  {day_and_time.get('start_time')} - {day_and_time.get('end_time')}"
            for day_and_time in self.class_days_and_times
        ]
        return f"{self.name.course_name}, {', '.join(formatted_days_and_times)}"
        # return f"{self.name.course_name} - {', '.join(self.class_days_and_times)}"
    



class CourseStudent(models.Model) :
    COURSE_STATUS_CHOICES = (
        ('passed', 'Passed'),
        ('active', 'Active'),
        ('failed', 'Failed'),
        ('deleted', 'Deleted'),
    )
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    course = models.ForeignKey(TermCourse, on_delete=models.PROTECT)
    # course = models.ForeignKey(ApprovedCourse, on_delete=models.PROTECT)
    course_status = models.CharField(max_length=10, choices=COURSE_STATUS_CHOICES)
    student_score = models.FloatField(max_length=20, null=True, blank=True)
    term_taken = models.ForeignKey('Term', on_delete=models.PROTECT) # should be deleted !!!!!!
    
    def __str__(self) :
        return f"{self.student.username} - {self.course.name.course_name}"
    
    
class RegistrationRequest(models.Model) :
    CONFIRMATION_STATUS_CHOICES = (
        ('not send', 'Not Send'),
        ('waiting', 'Waiting'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    )
    term = models.ForeignKey(Term, on_delete=models.PROTECT)
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    courses = models.ManyToManyField(TermCourse, null=True, blank=True)
    confirmation_status = models.CharField(max_length=10, choices=CONFIRMATION_STATUS_CHOICES, default='Not Send')
    
    
class RemovalAndExtensionRequest(models.Model) :
    CONFIRMATION_STATUS_CHOICES = (
        ('not send', 'Not Send'),
        ('waiting', 'Waiting'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    )
    term = models.ForeignKey(Term, on_delete=models.PROTECT)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    removed_courses = models.ManyToManyField(TermCourse, related_name="removed_courses", null=True, blank=True)
    extended_courses = models.ManyToManyField(TermCourse, related_name="extended_courses", null=True, blank=True)
    confirmation_status = models.CharField(max_length=10, choices=CONFIRMATION_STATUS_CHOICES, default='Not Send')
    
    
    
class ReconsiderationRequest(models.Model) :
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(CourseStudent, on_delete=models.CASCADE, unique=True)
    reconsideration_text = models.TextField(null=True, blank=True)
    reconsideration_response = models.TextField(null=True, blank=True)

    
    
class EmergencyRemovalRequest(models.Model) :
    REQUEST_RESULT_CHOICES = (
        ('acc', 'Accepted'),
        ('rjc', 'Rejected'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(TermCourse, on_delete=models.CASCADE)
    request_result = models.CharField(max_length=10, choices=REQUEST_RESULT_CHOICES)
    student_explanation = models.TextField(null=True, blank=True)
    educational_assistant_explanation = models.TextField(null=True, blank=True)
    
    
class TermRemovalRequest(models.Model) :
    REQUEST_RESULT_CHOICES = (
        ('acc', 'Accepted'),
        ('rjc', 'Rejected'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    request_result = models.CharField(max_length=10, choices=REQUEST_RESULT_CHOICES)
    student_explanation = models.TextField(null=True, blank=True)
    with_academic_years = models.BooleanField() # if true : removed term count in years, if false : removed term doesn't count in years
    educational_assistant_explanation = models.TextField(null=True, blank=True)
    

class EnrollmentCertificateRequest(models.Model) :
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    enrollment_certificate = models.FileField(null=True, blank=True) # should be editted
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    place_of_issue = models.TextField(max_length=100)
    
    
    