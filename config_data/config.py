import os
from peewee import *
from dotenv import load_dotenv, find_dotenv



if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

DEFAULT_COMMANDS = (
    ('start', "Запустить бота"),
    ('meet', "Перейти к meet"),
    ('help', "Вывести справку"),

)

# Подключение к базе данных SQLite
db = SqliteDatabase('users.db')

# Определяем модель для хранения информации о пользователях
class User(Model):
    user_id = IntegerField(unique=True)  # ID пользователя Telegram
    username = CharField()               # Имя пользователя (username)
    email = CharField(null=True)         # Поле для email, не обязательно для заполнения

    class Meta:
        database = db  # Связь с базой данных

# Создание таблицы, если ее еще нет
db.connect()
db.create_tables([User])