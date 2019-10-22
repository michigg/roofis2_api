FROM python:3.8-alpine

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm /requirements.txt

WORKDIR app
COPY src .

CMD ["python3", "app.py"]