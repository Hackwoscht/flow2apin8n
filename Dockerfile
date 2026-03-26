FROM python:3.11-slim

WORKDIR /app

# Python-Abhaengigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
