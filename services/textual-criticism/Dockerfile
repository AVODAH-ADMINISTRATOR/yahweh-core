FROM python:3.10-slim

WORKDIR /app

ENV HOME=/root
ENV YAHWEH_CORE_HOME=/root/yahweh-core

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY tests/ tests/

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
