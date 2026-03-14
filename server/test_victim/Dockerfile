# Используем легковесный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /victim_server

# Копируем файл приложения в контейнер
COPY victim_server.py .

# Открываем порт, который использует сервер
EXPOSE 9999

# Запускаем сервер
CMD ["python", "victim_server.py"]