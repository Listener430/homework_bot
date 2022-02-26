import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщения ботом"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        message = f"Не удалось отправить сообщение: {error}"
        logger.error("Не удалось отправить сообщение: {error}")
    else:
        logger.info("Сообщение успешно отправлено")


def get_api_answer(current_timestamp):
    """Получение ответа с ENDPOINT."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != 200:
        logger.error("ENDPOINT не доступен")
        raise Exception
    response = homework_statuses.json()
    return response


def check_response(response):
    """Проверка ответа."""
    homework = response["homeworks"]
    if not isinstance(homework, list):
        logger.error("`homeworks` домашки приходят не в виде списка")
        raise ValueError
    return homework


def parse_status(homework):
    """Получение статуса ответа"""
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    if not homework_status in HOMEWORK_STATUSES:
        logger.error("Такого статуса нет")
        raise KeyError
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов"""
    if PRACTICUM_TOKEN == None:
        logger.critical("PRACTICUM_TOKEN пустой")
        return False
    if TELEGRAM_TOKEN == None:
        logger.critical("TELEGRAM_TOKEN пустой")
        return False
    if TELEGRAM_CHAT_ID == None:
        logger.critical("TELEGRAM_CHAT_ID пустой")
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    old_message = ""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            message = parse_status(homework)
            if old_message != message:
                send_message(bot, message)
            else:
                logger.debug("Отсутствие новых статусов")
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            if old_message != message:
                send_message(bot, message)
            logger.error("Сбой в работе программы: {error}")
            time.sleep(RETRY_TIME)
            old_message = message
        else:
            old_message = message


if __name__ == "__main__":
    main()
