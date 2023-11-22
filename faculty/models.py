from django.db import models


class Faculty(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Major(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.name

    def get_department_choices(self):
        department_choices = Department.objects.filter(
            faculty=self.faculty
        ).values_list("name", "name")
        return department_choices

    def save(self, *args, **kwargs):
        if not self.department:
            self.department = None
            self._choices = self.get_department_choices()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["name"]


class ApprovedCourse(models.Model):
    COURSE_TYPE_CHOICES = (
        ("general", "Genaral"),
        ("specialized", "Specialized"),
        ("basic", "Basic"),
        ("theorical", "Theorical"),
        ("practical", "Practical"),
    )
    course_name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    pre_requisites = models.ManyToManyField(
        "self", symmetrical=False, null=True,
        blank=True, related_name="prerequisites",
    )
    co_requisites = models.ManyToManyField(
        "self", symmetrical=False, null=True,
        blank=True, related_name="corequisites",
    )

    units = models.IntegerField()
    course_type = models.CharField(max_length=100, choices=COURSE_TYPE_CHOICES)
    
    def __str__(self):
        return self.course_name
