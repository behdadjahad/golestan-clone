from django.test import TestCase
from django.utils import timezone
from faculty.models import Faculty, Major
from term.models import *


class TermModelTest(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(name="test_faculty")
        self.major = Major.objects.create(name="test_major", faculty=self.faculty, department="test_department")
        self.professor = Professor.objects.create(username="test_professor" ,professor_number="12345", faculty=self.faculty, major="math", expertise="math", degree="phd")
        self.course = ApprovedCourse.objects.create(course_name="test_course1", faculty=self.faculty, units=3, course_type="general")
        self.term = Term.objects.create(
            term_name='Test Term',
            unit_selection_start_time=timezone.now(),
            unit_selection_end_time=timezone.now(),
            courses_start_time=timezone.now(),
            courses_end_time=timezone.now(),
            repairing_unit_selection_start_time=timezone.now(),
            repairing_unit_selection_end_time=timezone.now(),
            emergency_deletion_end_time=timezone.now(),
            exams_start_time=timezone.now(),
            term_end_time=timezone.now(),
        )
        self.student1 = Student.objects.create(
            username="test_student",
            student_number="12345",
            intrance_term=self.term,
            faculty=self.faculty,
            major=self.major,
            supervisor=self.professor,
            militery_service_status="exempt",
            )
        
        self.term_course = TermCourse.objects.create(
            name=self.course,
            class_days_and_times=[{"day": "Sat", "time": "13:00"},{"day": "Mon", "time": "13:00"},],
            exam_time=timezone.now(),
            exam_place='Test Exam Place',
            course_professor=self.professor,
            course_capacity=30,
            term=self.term,
        )
        
    def test_create_term(self):

        self.term.students_registered.add(self.student1)
        self.term.professor_registered.add(self.professor)
        self.term.term_courses.add(self.term_course)

        self.assertEqual(self.term.term_name, 'Test Term')
        self.assertEqual(self.term.students_registered.first(), self.student1)
        self.assertEqual(self.term.professor_registered.first(), self.professor)
        self.assertEqual(self.term.term_courses.first(), self.term_course)
        
        
class TermCourseModelTest(TestCase):
    def setUp(self) :
        self.faculty = Faculty.objects.create(name="test_faculty")
        self.major = Major.objects.create(name="test_major", faculty=self.faculty, department="test_department")
        self.professor = Professor.objects.create(username="test_professor" ,professor_number="12345", faculty=self.faculty, major="math", expertise="math", degree="phd")
        self.course = ApprovedCourse.objects.create(course_name="test_course1", faculty=self.faculty, units=3, course_type="general")
        self.term = Term.objects.create(
            term_name='Test Term',
            unit_selection_start_time=timezone.now(),
            unit_selection_end_time=timezone.now(),
            courses_start_time=timezone.now(),
            courses_end_time=timezone.now(),
            repairing_unit_selection_start_time=timezone.now(),
            repairing_unit_selection_end_time=timezone.now(),
            emergency_deletion_end_time=timezone.now(),
            exams_start_time=timezone.now(),
            term_end_time=timezone.now(),
        )
        self.term_course = TermCourse.objects.create(
            name=self.course,
            class_days_and_times=[{"day": "Sat", "time": "13:00"},{"day": "Mon", "time": "13:00"},],
            exam_time=timezone.now(),
            exam_place='Test Exam Place',
            course_professor=self.professor,
            course_capacity=30,
            term=self.term,
        )
        
    def test_create_termcourse(self):
        self.assertEqual(self.term_course.name, self.course)
        self.assertEqual(self.term_course.course_professor, self.professor)
        self.assertEqual(self.term_course.term, self.term)
        self.assertEqual(self.term_course.course_capacity, 30)
        
        
class CourseStudentModelTests(TestCase) :
    def setUp(self) :
        self.faculty = Faculty.objects.create(name="test_faculty")
        self.major = Major.objects.create(name="test_major", faculty=self.faculty, department="test_department")
        self.professor = Professor.objects.create(username="test_professor" ,professor_number="12345", faculty=self.faculty, major="math", expertise="math", degree="phd")
        self.course = ApprovedCourse.objects.create(course_name="test_course1", faculty=self.faculty, units=3, course_type="general")
        self.term = Term.objects.create(
            term_name='Test Term',
            unit_selection_start_time=timezone.now(),
            unit_selection_end_time=timezone.now(),
            courses_start_time=timezone.now(),
            courses_end_time=timezone.now(),
            repairing_unit_selection_start_time=timezone.now(),
            repairing_unit_selection_end_time=timezone.now(),
            emergency_deletion_end_time=timezone.now(),
            exams_start_time=timezone.now(),
            term_end_time=timezone.now(),
        )
        self.student1 = Student.objects.create(
            username="test_student",
            student_number="12345",
            intrance_term=self.term,
            faculty=self.faculty,
            major=self.major,
            supervisor=self.professor,
            militery_service_status="exempt",
            )
        self.coursestudent = CourseStudent.objects.create(student=self.student1, course=self.course, course_status="passed", student_score=18, term_taken=self.term)
    
    def test_create_coursestudent(self) :
        self.assertEqual(self.coursestudent.student, self.student1)
        self.assertEqual(self.coursestudent.course, self.course)
        self.assertEqual(self.coursestudent.term_taken, self.term)
        self.assertEqual(self.coursestudent.course_status, 'passed')