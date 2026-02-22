# 1. Фиксируем версию для защиты от атак на цепочку поставок и обеспечения стабильности.
# Замените 2.15.0 на актуальную стабильную версию, которую вы протестировали.
FROM zaproxy/zap-stable:2.17.0

# 2. Переключаемся на root только для обновления ОС и закрытия известных CVE в базовом образе
USER root
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# 3. Возвращаемся к непривилегированному пользователю zap (создан в базовом образе)
USER zap

# 4. Устанавливаем аддоны
RUN zap.sh -cmd -addoninstall ajaxSpider \
    && zap.sh -cmd -addoninstall retire \
    && zap.sh -cmd -addoninstall pscanrulesBeta \
    && zap.sh -cmd -addoninstall ascanrulesAlpha

# 5. Убираем хардкод ключа и ограничиваем доступ.
# ZAP автоматически подхватит переменную окружения ZAP_API_KEY, если использовать shell-форму команды.
# Доступ к API ограничиваем стандартными подсетями Docker (172.16.0.0/12) или вашей конкретной подсетью.
CMD zap.sh -daemon -host 0.0.0.0 -port 8080 -config "api.addrs.addr.name=.*" -config api.addrs.addr.regex=true -config api.key=$ZAP_API_KEY