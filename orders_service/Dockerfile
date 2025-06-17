FROM python:3.10-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN touch orders.db && chmod 666 orders.db

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
