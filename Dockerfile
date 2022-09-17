FROM python:latest
RUN pip install pip --upgrade

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "run:app", "--workers", "1", "--timeout", "300"]