FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "gestion_escolar.wsgi:application", "--bind", "0.0.0.0:8000"]
