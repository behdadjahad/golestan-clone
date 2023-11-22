# Generated by Django 4.1.4 on 2023-11-22 14:24

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('faculty', '0001_initial'),
        ('term', '0001_initial'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ITManager',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('itmanager_number', models.CharField(max_length=10, unique=True)),
            ],
            options={
                'verbose_name_plural': 'ITManager',
            },
            bases=('user.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Professor',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('professor_number', models.CharField(max_length=10, unique=True)),
                ('major', models.CharField(max_length=100)),
                ('expertise', models.CharField(max_length=100)),
                ('degree', models.CharField(max_length=100)),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='faculty.faculty')),
            ],
            options={
                'verbose_name_plural': 'Professor',
            },
            bases=('user.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('student_number', models.CharField(max_length=10, unique=True)),
                ('intrance_year', models.DateField(auto_now_add=True)),
                ('years', models.PositiveIntegerField(default=0)),
                ('militery_service_status', models.CharField(choices=[('exempt', 'Exempt'), ('cardservice', 'CardService'), ('educationalexempt', 'EducationalExempt')], max_length=20)),
                ('courses', models.ManyToManyField(blank=True, null=True, related_name='enrolled_students', to='term.coursestudent')),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='faculty.faculty')),
                ('intrance_term', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='term.term')),
                ('major', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='faculty.major')),
                ('supervisor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='account.professor')),
            ],
            options={
                'verbose_name_plural': 'Student',
            },
            bases=('user.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='EducationalAssistant',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('educational_assistant_number', models.CharField(max_length=10, unique=True)),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='faculty.faculty')),
                ('major', models.ManyToManyField(to='faculty.major')),
            ],
            options={
                'verbose_name_plural': 'EducationalAssistant',
            },
            bases=('user.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
