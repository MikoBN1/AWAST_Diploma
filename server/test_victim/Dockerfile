FROM python:3.11-slim

WORKDIR /victim_server

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY victim_server.py .

EXPOSE 9999

CMD ["python", "victim_server.py"]