FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/s0md3v/XSStrike.git /app/xsstrike

WORKDIR /app/xsstrike

RUN pip install --no-cache-dir -r requirements.txt

COPY api_wrapper.py /app/api_wrapper.py

RUN pip install --no-cache-dir flask

EXPOSE 5000

CMD ["python", "/app/api_wrapper.py"]
