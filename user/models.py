from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    profile_pic = models.ImageField(upload_to="static/", blank=True)
    phone_number = models.CharField( max_length=11, blank=True, null=True, verbose_name='phone number')
    national_id = models.CharField(max_length=10, blank=True, null=True, verbose_name='national id')
    birth_date = models.DateField(blank=True, null=True, verbose_name='birth date')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='updated at')

    def __str__(self):
        return self.username
    