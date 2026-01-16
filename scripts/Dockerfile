FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir psycopg2-binary

COPY load_generator.py .

CMD ["python", "load_generator.py", "--mode", "light"]
