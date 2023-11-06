from django.test import TestCase
from account.models import Professor, Student, EducationalAssistant, ITManager
from faculty.models import Faculty, ApprovedCourse, Major
from term.models import Term, CourseStudent
from django.utils import timezone
from datetime import date

class StudentModelTests(TestCase) :
    def setUp(self) :
        term1 = Term.objects.create(
            term_name="test_term1",
            unit_selection_start_time=timezone.now(),
            unit_selection_end_time=timezone.now(),
            courses_start_time=date(2023, 11, 4),
            courses_end_time=date(2023, 11, 4),
            repairing_unit_selection_start_time=timezone.now(),
            repairing_unit_selection_end_time=timezone.now(),
            emergency_deletion_end_time=timezone.now(),
            exams_start_time=date(2023, 11, 4),
            term_end_time=date(2023, 11, 4),
            )
        term2 = Term.objects.create(
            term_name="test_term2",
            unit_selection_start_time=timezone.now(),
            unit_selection_end_time=timezone.now(),
            courses_start_time=date(2023, 11, 4),
            courses_end_time=date(2023, 11, 4),
            repairing_unit_selection_start_time=timezone.now(),
            repairing_unit_selection_end_time=timezone.now(),
            emergency_deletion_end_time=timezone.now(),
            exams_start_time=date(2023, 11, 4),
            term_end_time=date(2023, 11, 4),
            )
        faculty = Faculty.objects.create(name="test_faculty")
        major = Major.objects.create(name="test_major", faculty=faculty, department="test_department")
        course1 = ApprovedCourse.objects.create(course_name="test_course1", faculty=faculty, units=3, course_type="general")
        course2 = ApprovedCourse.objects.create(course_name="test_course2", faculty=faculty, units=2, course_type="basic")
        course3 = ApprovedCourse.objects.create(course_name="test_course3", faculty=faculty, units=1, course_type="practical")
        course4 = ApprovedCourse.objects.create(course_name="test_course4", faculty=faculty, units=4, course_type="specialized")
        professor = Professor.objects.create(username="test_professor" ,professor_number="12345", faculty=faculty, major="math", expertise="math", degree="phd")
        student1 = Student.objects.create(
            username="test_student",
            student_number="12345",
            intrance_term=term1,
            faculty=faculty,
            major=major,
            supervisor=professor,
            militery_service_status="exempt",
            )
        student2 = Student.objects.create(
            username="test_student2",
            student_number="123456",
            intrance_term=term1,
            faculty=faculty,
            major=major,
            supervisor=professor,
            militery_service_status="exempt",
            )
        CourseStudent.objects.create(student=student1, course=course1, course_status="passed", student_score=18, term_taken=term1)
        CourseStudent.objects.create(student=student1, course=course2, course_status="passed", student_score=15, term_taken=term1)
        CourseStudent.objects.create(student=student1, course=course3, course_status="passed", student_score=14, term_taken=term1)
        CourseStudent.objects.create(student=student1, course=course4, course_status="active", term_taken=term2)
        CourseStudent.objects.create(student=student2, course=course1, course_status="passed", student_score=13, term_taken=term1)
        
    def test_create_student(self) :
        student = Student.objects.get(username="test_student")
        faculty = Faculty.objects.get(name="test_faculty")
        term = Term.objects.get(term_name="test_term1")
        major = Major.objects.get(name="test_major")
        professor = Professor.objects.get(username="test_professor")
        
        self.assertEqual(student.username, "test_student")
        self.assertEqual(student.student_number, "12345")
        self.assertEqual(student.intrance_term, term)
        self.assertEqual(student.faculty, faculty)
        self.assertEqual(student.major, major)
        self.assertEqual(student.supervisor, professor)
        self.assertEqual(student.militery_service_status, "exempt")
        
    def test_term_score(self) :
        student = Student.objects.get(username="test_student")
        term1 = Term.objects.get(term_name="test_term1")
        term2 = Term.objects.get(term_name="test_term2")
        
        self.assertEqual(round(student.term_score(term1), 2), 16.33)
        self.assertEqual(student.term_score(term2), 0.0)
        
    def test_gpa(self) :
        student = Student.objects.get(username="test_student")
        self.assertEqual(round(student.gpa, 2), 16.33)
        
    def test_active_courses(self) :
        student = Student.objects.get(username="test_student")
        coursestudent = CourseStudent.objects.filter(student=student, course_status="active")
        acc_courses = []
        for course in student.active_courses :
            acc_courses.append(course.coursestudent_set.first()) 
        self.assertEqual(acc_courses, list(coursestudent))
        
    def test_passed_courses(self) :
        student = Student.objects.get(username="test_student")
        coursestudent = CourseStudent.objects.filter(student=student, course_status="passed")
        pss_courses = []
        for course in student.passed_courses :
            pss_courses.append(course.coursestudent_set.first()) 
        self.assertEqual(pss_courses, list(coursestudent))
        

class ProfessorModelTests(TestCase) :
    def setUp(self) :
        faculty = Faculty.objects.create(name="test_faculty")
        Professor.objects.create(username="test_professor" ,professor_number="12345", faculty=faculty, major="math", expertise="math", degree="phd")
        ApprovedCourse.objects.create(course_name="test_course1", faculty=faculty, units=3, course_type="general")
        
        
    def test_create_professor(self) :
        professor = Professor.objects.get(username="test_professor")
        faculty = Faculty.objects.get(name="test_faculty")
        course1 = ApprovedCourse.objects.get(course_name="test_course1")
        
        self.assertEqual(professor.username, "test_professor")
        self.assertEqual(professor.professor_number, "12345")
        self.assertEqual(professor.faculty, faculty)
        self.assertEqual(professor.major, "math")
        self.assertEqual(professor.expertise, "math")
        self.assertEqual(professor.degree, "phd")
        
        self.assertEqual(professor.presented_courses.all().count(), 0)
        professor.presented_courses.add(course1)
        professor = Professor.objects.get(username="test_professor")
        self.assertEqual(professor.presented_courses.all().count(), 1)


class ITManagerModelTests(TestCase) :
    def setUp(self) :
        ITManager.objects.create(username="test_itmanager" ,itmanager_number="12345")

        
        
    def test_create_itmanager(self) :
        itmanager = ITManager.objects.get(username="test_itmanager")
        
        self.assertEqual(itmanager.username, "test_itmanager")
        self.assertEqual(itmanager.itmanager_number, "12345")

        
class EducationalAssistantModelTests(TestCase) :
    def setUp(self) :
        faculty = Faculty.objects.create(name="test_faculty")
        mjr = Major.objects.create(name="test_major", faculty=faculty, department="test_department")
        ea = EducationalAssistant.objects.create(username="test_educationalassistant" ,educational_assistant_number="12345", faculty=faculty)
        ea.major.add(mjr)
        
    def test_create_educationalassistant(self) :
        educationalassistant = EducationalAssistant.objects.get(username="test_educationalassistant")
        faculty = Faculty.objects.get(name="test_faculty")
        major = Major.objects.get(name="test_major")
        
        self.assertEqual(educationalassistant.username, "test_educationalassistant")
        self.assertEqual(educationalassistant.educational_assistant_number, "12345")
        self.assertEqual(educationalassistant.faculty, faculty)
        self.assertEqual(educationalassistant.major.all().first(), major)
        