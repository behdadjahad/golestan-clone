FROM python:3.8

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SUPERUSER_PASSWORD admin

RUN mkdir /app
WORKDIR /app

RUN mkdir logs
RUN touch logs/critical.log
RUN touch logs/info.log
RUN touch logs/error.log
COPY . ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD python3 manage.py makemigrations --noinput; \
    python3 manage.py migrate --noinput; \
    python3 manage.py createsuperuser --user admin --email admin@localhost --noinput; \
    python3 manage.py runserver