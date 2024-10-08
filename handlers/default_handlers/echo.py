import time

from telebot.types import Message
from loader import bot

from process.openai_request import *
import logging
from transcript.transcripting import transcription_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

requests_array = []


@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio(message: Message):
    user_id = message.chat.id
    logger.info(f"Получено аудиосообщение от пользователя с ID {user_id}")

    time.sleep(2)
    bot.send_message(user_id, "Your audio file is accepted. Please Wait ...")
    bot.send_sticker(chat_id=user_id, sticker="CAACAgIAAxkBAAEKnGplOmWMrOTU1wLE0-7HsvsH3AmfFAACfAcAAkb7rARWx40W6tQRKjAE")

    try:
        # Если это аудиофайл
        if message.content_type == 'audio':
            file_id = message.audio.file_id
            logger.info("Аудиофайл получен")
        # Если это голосовое сообщение
        elif message.content_type == 'voice':
            file_id = message.voice.file_id
            logger.info("Голосовое сообщение получено")

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        logger.info(f"Файл успешно скачан: {file_info.file_path}")

        # Сохраняем файл локально
        with open("audio.ogg", 'wb') as new_file:
            new_file.write(downloaded_file)
        logger.info("Аудиофайл сохранен как audio.ogg")

        # Транскрипция аудиофайла
        transcript = transcription_file("audio.ogg", 2)
        logger.info("Транскрипция завершена")

        # Сохранение транскрипции в txt файл
        with open("transcripts.txt", "w", encoding="utf-8") as file:
            file.write(transcript)
        logger.info("Транскрипция сохранена в transcripts.txt")

        # Обработка запроса
        db = read_file_request()
        summary = process_gpt_request(db, "/ask What's the diagnosis?")
        logger.info("Запрос GPT обработан")

        save_to_pdf("summary.pdf", summary)
        logger.info("Ответ сохранен в summary.pdf")

        # Отправка PDF пользователю
        with open("summary.pdf", "rb") as pdf_file:
            bot.send_message(user_id, "Thank you for your patience! Here is your file!!!")
            time.sleep(1)
            bot.send_document(user_id, pdf_file)
        logger.info(f"PDF файл отправлен пользователю с ID {user_id}")

        # Очистка временных файлов
        os.remove("audio.ogg")
        os.remove("transcripts.txt")
        os.remove("summary.pdf")
        logger.info("Временные файлы удалены")

    except Exception as e:
        logger.error(f"Ошибка при обработке аудиофайла: {e}")
        bot.send_message(user_id, "An error occurred while processing your file. Please try again later.")


from fpdf import FPDF

def save_to_pdf(filename, text):
    """
    Сохраняет текст в файл PDF с поддержкой Unicode для русского и английского текста.
    """
    pdf = FPDF()
    pdf.add_page()

    # Добавляем обычный и полужирный шрифты с поддержкой Unicode
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)

    # логотип
    pdf.image('medical_symbol.png', x=85, y=20, w=40)

    # Заголовок
    pdf.ln(60)  # вниз
    pdf.set_font("DejaVu", 'B', size=20)
    pdf.cell(200, 10, "Медицинское заключение", ln=True, align='C')

    # Основной текст
    pdf.set_font("DejaVu", size=12)
    lines = text.split("\n")

    right_margin = 20  # Отступ от правого края в мм
    pdf.set_right_margin(right_margin)

    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            pdf.set_font("DejaVu", 'B', size=12)
            pdf.cell(90, 10, key + ":", ln=False)

            # Сдвигаем курсор на 20 мм влево перед выводом значения
            x = pdf.get_x() - 20
            pdf.set_x(x)

            pdf.set_font("DejaVu", size=12)
            pdf.multi_cell(110, 10, value)
        else:
            pdf.multi_cell(200 - right_margin, 10, line, align='C')

    pdf.output(filename)



@bot.message_handler(content_types=['text', 'audio', 'voice'])
def bot_echo(message: Message):
    logger.info(f"Получено текстовое сообщение: {message.text}")
    user_request = message.text

    if user_request.startswith("/ask "):
        try:
            file_request = read_file_request()
            request_obj = {
                "user_request": user_request,
                "file_request": file_request,
            }
            requests_array.append(request_obj)
            response = process_gpt_request(file_request, user_request)
            bot.send_message(message.chat.id, response)
            logger.info("Запрос успешно обработан через GPT")
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            bot.send_message(message.chat.id, "An error occurred. Please try again.")
    else:
        try:
            response = request_chat(user_request)
            bot.send_message(message.chat.id, response)
            logger.info("Ответ на запрос отправлен")
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса через Chat API: {e}")
            bot.send_message(message.chat.id, "An error occurred. Please try again.")

