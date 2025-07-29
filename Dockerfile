FROM python:3.11-slim

WORKDIR /bot

COPY requirements.txt .


RUN apt-get update && apt-get install -y gcc libpq-dev

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
