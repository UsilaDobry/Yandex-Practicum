# устанавливаем базовый образ
FROM python:3.10.8

# устанавливаем метаданные
MAINTAINER Eduard Bidenko <usila-dobry@yandex.ru>

# устанавливаем директорию для придложения
WORKDIR /usr/src/dash_app

# копируем все файлы в контейнер
COPY . .

# устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# укажим номер порта, который контейнер должен предоставить
EXPOSE 8050

# команда для запуска
# CMD ["python", "./dash_app.py"]
ENTRYPOINT ["python", "./dash_app.py"]