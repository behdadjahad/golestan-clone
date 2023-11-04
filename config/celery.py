from celery import Celery
import os

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTING_MODULE', 'golestan-clone.settings')
app = Celery('golestan-clone')

# Load tasks from all registered Django app configs
app.autodiscover_tasks()