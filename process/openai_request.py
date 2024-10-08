import requests
import openai
from langchain.schema import Document
from datetime import datetime
from config_data.config import *

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains.openai_functions import (
    create_structured_output_chain,
)
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ChatOpenAI.api_key = os.getenv('OPENAI_API_KEY')
embeddings = OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_API_KEY'))


def read_file_request():
    """
    Функция для чтения запроса из файла
    :return:
    """
    try:
        with open("transcripts.txt", "r", encoding="utf-8") as file:
            file_request = file.read()
        logger.info("Файл успешно прочитан.")
        transcript = [Document(page_content=file_request, metadata={"source": "local"})]
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
        docs = text_splitter.split_documents(transcript)
        db = FAISS.from_documents(docs, embeddings)
        logger.info("Документы успешно разделены и добавлены в базу данных.")
        return db

    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        raise


def process_gpt_request(db, user_request, k=4):
    """
    Функция для обработки запроса в GPT
    :param db:
    :param user_request:
    :param k:
    :return:
    """
    try:
        logger.info(f"Обработка запроса пользователя: {user_request}")
        docs = db.similarity_search(user_request, k=k)
        docs_page_content = " ".join([d.page_content for d in docs])
        logger.info("Найдено похожих документов: {}".format(len(docs)))

        chat = ChatOpenAI(model_name="gpt-4", temperature=0.8)

        template = """
        You're a doctor's assistant. Based on the transcript: {docs}
        Please provide a summary in the following format:
        Doctor's Name: ...
        Patient's Name: ...
        Symptoms: ...
        Diagnosis: ...
        Past Illnesses: ...
        Heredity: ...
        Allergic Reactions: ...
        Recommendations: ...

        Only use the factual information from the transcript.
        translate everything only into Russian
        """

        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = "Answer the following question: {question}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        json_schema = {
            "title": "Summary",
            "description": "Summary of the doctor-client conversation.",
            "type": "object",
            "properties": {
                "doctor_name": {"type": "string"},
                "patient_name": {"type": "string"},
                "symptoms": {"type": "string"},
                "diagnosis": {"type": "string"},
                "past_illnesses": {"type": "string"},
                "heredity": {"type": "string"},
                "allergic_reactions": {"type": "string"},
                "recommendations": {"type": "string"}
            },
            "required": ["doctor_name", "patient_name", "symptoms", "diagnosis"],
        }

        chain = create_structured_output_chain(json_schema, llm=chat, prompt=chat_prompt)
        response = chain.run(question=user_request, docs=docs_page_content)

        current_date = datetime.now().strftime('%Y-%m-%d')

        summary = f"Дата: {current_date}\n" \
                  f"Имя доктора: {response.get('doctor_name')}\n" \
                  f"Имя пациента: {response.get('patient_name')}\n" \
                  f"Симптомы: {response.get('symptoms')}\n" \
                  f"Диагноз: {response.get('diagnosis')}\n" \
                  f"Перенесенные болезни: {response.get('past_illnesses')}\n" \
                  f"Наследственность: {response.get('heredity')}\n" \
                  f"Аллергические реакции: {response.get('allergic_reactions')}\n" \
                  f"Рекомендации: {response.get('recommendations')}"

        logger.info("Запрос обработан успешно.")
        return summary

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        raise



def request_chat(user_request):
    """
    Отправка запроса в GPT через API OpenAI
    :param user_request: запрос пользователя
    :return: ответ GPT
    """
    try:
        logger.info(f"Отправка запроса в GPT: {user_request}")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": 'Your model response here.'},
                {"role": "user", "content": user_request},
            ],
        )

        if response and response.choices:
            response_text = response.choices[0].message['content']
            cleaned_response = response_text.strip()
            logger.info("Ответ от GPT успешно получен.")
            return cleaned_response
        else:
            logger.warning("Ответ от GPT пуст или отсутствует.")
            return None

    except Exception as e:
        logger.error(f"Ошибка при отправке запроса: {e}")
        raise