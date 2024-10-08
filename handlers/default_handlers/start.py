import logging
from telebot import types
from telebot.types import Message
from loader import bot

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@bot.message_handler(commands=['start'])
def bot_start(message: Message):
    user_id = message.chat.id
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name

    # Логируем получение команды /start
    logger.info(f"Команда /start получена от пользователя: {user_first_name} {user_last_name} (ID: {user_id})")

    bot.send_message(user_id, f'Hi, {user_first_name} {user_last_name}, поговорим?')
    logger.info(f"Отправлено приветственное сообщение пользователю: {user_first_name} {user_last_name} (ID: {user_id})")
