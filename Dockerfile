FROM hub.hamdocker.ir/library/python:3.11.2-slim

WORKDIR /app

COPY  requirements.txt /app/

RUN pip install -r requirements.txt

COPY . /app/

# RUN python manage.py migrate

EXPOSE 8000

CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ]
