FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p static/uploads/drivers

EXPOSE 7860

CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app
