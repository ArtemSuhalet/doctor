import os
import logging
from langchain.document_loaders import Blob
from langchain.document_loaders.parsers import OpenAIWhisperParser

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def transcription_file(path, max_participants):
    """
    Функция для транскрипции файла в текст
    :param path: путь к файлу для транскрипции
    :param max_participants: максимальное количество участников
    :return: текст транскрипции
    """

    try:
        logger.info(f"Начало транскрипции файла: {path}")

        # Инициализация парсера OpenAI Whisper
        parser = OpenAIWhisperParser(api_key=os.getenv('API_KEY'))
        docs = [c for c in parser.lazy_parse(Blob(path=path))]
        logger.info(f"Файл {path} успешно распознан")

        # Объединение всех частей транскрипции в один текст
        transcript = " ".join([d.page_content for d in docs])
        logger.info(f"Транскрипция завершена успешно, длина текста: {len(transcript)} символов")

        return transcript

    except Exception as e:
        logger.error(f"Ошибка при транскрипции файла {path}: {e}")
        raise
