FROM python:3.10-slim

# for immediate logging
ENV PYTHONUNBUFFERED=1 
# prevents .pyc generation 
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# PostgreSQL client for pg_isready
RUN apt-get update && \
    apt-get install -y git && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# if we are using entrypoint script for intial services start
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port","9000", "--reload"]