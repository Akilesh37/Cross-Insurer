FROM python:3.10-slim

WORKDIR /app

COPY services/gateway/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/gateway/ .

# Copy dashboard static files so gateway can serve them directly
COPY dashboard /app/dashboard

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
