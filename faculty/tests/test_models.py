from django.test import TestCase
from faculty.models import Faculty, Department, Major, ApprovedCourse


class FacultyModelTest(TestCase):
    def test_create_faculty(self):
        faculty = Faculty.objects.create(name="Engineering")
        self.assertEqual(str(faculty), "Engineering")


class DepartmentModelTest(TestCase):
    def test_create_department(self):
        faculty = Faculty.objects.create(name="Science")
        department = Department.objects.create(name="Physics", faculty=faculty)
        self.assertEqual(str(department), "Physics")


class MajorModelTest(TestCase):
    def test_create_major(self):
        faculty = Faculty.objects.create(name="Arts")
        department = Department.objects.create(name="History", faculty=faculty)
        major = Major.objects.create(
            name="Ancient History", faculty=faculty, department=department.name)
        self.assertEqual(str(major), "Ancient History")

    def test_major_department_choices(self):
        faculty = Faculty.objects.create(name="Medicine")
        department1 = Department.objects.create(
            name="Surgery", faculty=faculty)
        department2 = Department.objects.create(
            name="Anatomy", faculty=faculty)

        major = Major.objects.create(
            name="Cardiology", faculty=faculty, department=department1.name)
        self.assertEqual(major.department, department1.name)

        major = Major.objects.create(
            name="Neurology", faculty=faculty, department=department2.name)
        self.assertEqual(major.department, department2.name)


class ApprovedCourseModelTest(TestCase):
    def test_create_approved_course(self):
        faculty = Faculty.objects.create(name="Sample Faculty")
        course = ApprovedCourse.objects.create(course_name="Sample Course", faculty=faculty, units=3, course_type="general")
        self.assertEqual(course.course_name, "Sample Course")
        self.assertEqual(course.faculty, faculty)
        self.assertEqual(course.units, 3)
        self.assertEqual(course.course_type, "general")
