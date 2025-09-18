FROM zaproxy/zap-stable:latest

# Устанавливаем аддоны во время сборки
# используем zap.sh -cmd -addoninstall ... (поддерживается официальным образом)
RUN zap.sh -cmd -addoninstall ajaxSpider retire pscanrulesBeta ascanrulesAlpha

# Оставляем поведение запуска как в оригинальном образе
CMD ["zap.sh", "-daemon", "-host", "0.0.0.0", "-port", "8080", "-config", "api.addrs.addr.name=.*", "-config", "api.addrs.addr.regex=true", "-config", "api.key=changeme"]
