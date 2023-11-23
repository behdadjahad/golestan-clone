FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SUPERUSER_PASSWORD admin

RUN mkdir app
WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN mkdir logs
RUN touch logs/critical.log
RUN touch logs/warning.log
RUN touch logs/error.log
RUN touch logs/debug.log
RUN touch logs/info.log
COPY . ./

CMD python3 manage.py makemigrations user account faculty term --noinput; \
    python3 manage.py migrate --noinput; \
    python3 manage.py createsuperuser --user admin --email admin@localhost --noinput; \
    python3 manage.py runserver 0.0.0.0:8000