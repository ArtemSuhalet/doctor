import logging
from telebot import types
from telebot.types import Message

from config_data.config import User
from loader import bot

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STATE_AWAITING_EMAIL = 'awaiting_email'
STATE_NORMAL = 'normal'

# Словарь для хранения состояний пользователя
user_states = {}

@bot.message_handler(commands=['start'])
def bot_start(message: Message):
    user_id = message.chat.id
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    username = message.from_user.username

    # Логируем получение команды /start
    logger.info(f"Команда /start получена от пользователя: {user_first_name} {user_last_name} (ID: {user_id})")

    # Проверяем, есть ли пользователь в базе данных
    user, created = User.get_or_create(user_id=user_id, defaults={'username': username})

    if created:
        logger.info(f"Новый пользователь добавлен в базу данных: {username} (ID: {user_id})")
    else:
        logger.info(f"Пользователь уже существует в базе данных: {username} (ID: {user_id})")

    # Отправляем приветственное сообщение
    bot.send_message(user_id, f'Hi, {user_first_name} {user_last_name}!')
    logger.info(f"Отправлено приветственное сообщение пользователю: {user_first_name} {user_last_name} (ID: {user_id})")

    # Проверка наличия электронной почты
    if not user.email:
        bot.send_message(
            user_id,
            "У вас не указана электронная почта. Вы можете ввести её сейчас или отправить 'нет', если не хотите вводить email."
        )
        logger.info(f"Пользователю {user_first_name} {user_last_name} предложено ввести email или нет.")

        # Устанавливаем состояние ожидания email
        user_states[user_id] = STATE_AWAITING_EMAIL
    else:
        bot.send_message(user_id, "Ваш email уже сохранен. Можете продолжать использовать бота.")
        logger.info(f"Email пользователя уже существует: {user.email} (ID: {user_id})")


# Обработчик ввода email или отказа
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == STATE_AWAITING_EMAIL)
def receive_email_or_decline(message: Message):
    user_id = message.chat.id
    user_response = message.text

    if user_response.lower() == 'нет':
        # Пользователь отказался вводить email
        bot.send_message(user_id, "Вы отказались от ввода email. Можете продолжать использование бота.")
        logger.info(f"Пользователь {user_id} отказался вводить email.")

        # Сбрасываем состояние ожидания email
        user_states[user_id] = STATE_NORMAL
    else:
        # Проверка валидности email
        if "@" not in user_response:
            bot.send_message(user_id,
                             "Это не похоже на правильный email. Пожалуйста, введите корректный email или отправьте 'нет'.")
            return

        try:
            # Находим пользователя и обновляем его email
            user = User.get(User.user_id == user_id)
            user.email = user_response
            user.save()

            bot.send_message(user_id, "Ваш email успешно сохранен. Можете продолжать использование бота.")
            logger.info(f"Email пользователя обновлен: {user_response} (ID: {user_id})")

            # Сбрасываем состояние ожидания email
            user_states[user_id] = STATE_NORMAL
        except User.DoesNotExist:
            bot.send_message(user_id, "Произошла ошибка. Пожалуйста, используйте команду /start сначала.")
            logger.error(f"Не удалось найти пользователя с ID: {user_id}")
            user_states[user_id] = STATE_NORMAL



# # Обработка команды для добавления email
# @bot.message_handler(commands=['email'])
# def set_email(message: Message):
#     user_id = message.chat.id
#     email = message.text.split(maxsplit=1)[1]  # Извлекаем email после команды
#
#     try:
#         # Находим пользователя и обновляем его email
#         user = User.get(User.user_id == user_id)
#         user.email = email
#         user.save()
#
#         bot.send_message(user_id, "Ваш email успешно сохранен.")
#         logger.info(f"Email пользователя обновлен: {email} (ID: {user_id})")
#     except User.DoesNotExist:
#         bot.send_message(user_id, "Пожалуйста, используйте команду /start сначала.")
#         logger.error(f"Не удалось найти пользователя с ID: {user_id}")
