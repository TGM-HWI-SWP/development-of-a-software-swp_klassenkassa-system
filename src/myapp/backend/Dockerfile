FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

ENV PYTHONPATH=/app/src

EXPOSE 8000

# später ersetzen wir das durch deinen echten Backend-Start (FastAPI)
CMD ["python", "-m", "myapp.backend.api"]
