FROM python:3.10.12

WORKDIR /app

COPY server.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python3","server.py"]