FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /app/sqlmap

EXPOSE 8775

CMD ["python", "/app/sqlmap/sqlmapapi.py", "-s", "-H", "0.0.0.0", "-p", "8775"]
