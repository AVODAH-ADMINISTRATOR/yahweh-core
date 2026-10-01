FROM python:3.10-slim

WORKDIR /app
COPY . /app/council_os

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/root
ENV YAHWEH_CORE_HOME=/root/yahweh-core
ENV COUNCIL_OS_DOMAIN=governance

EXPOSE 8106

CMD ["python", "-m", "council_os.service"]
