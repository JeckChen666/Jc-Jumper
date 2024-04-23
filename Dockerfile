FROM python:3.12-slim

ARG VERSION=1.0.0

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
