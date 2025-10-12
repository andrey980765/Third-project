# Photo Metadata — JSON / XML

Это Django-приложение позволяет:

- Вводить метаданные фотографий через веб-форму;
- Сохранять данные в формате JSON или XML;
- Загружать существующие JSON/XML файлы на сервер;
- Просматривать список всех файлов и содержимое каждого файла;
- Проверять валидность данных и файлов.

---

## 🛠 Технологии

- Python 3.11+
- Django 5.2
- HTML/CSS
- Базовые знания JSON и XML

---

## ⚡ Установка

1. Скачать архив
2. Создайте виртуальное окружение и активируйте его:
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
3. Установите зависимости:
pip install -r requirements.txt
4. Примените миграции:
python manage.py migrate
5. Запустите сервер разработки:
python manage.py runserver
6. Откройте в браузере:
http://127.0.0.1:8000/

