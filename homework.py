import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv
from exceptions import NoMessageSendError, GetApiAnswerError, TokenIsEmptyError

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_RETRY_TIME = 600

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
    """Отправка сообщения ботом."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        raise NoMessageSendError
    else:
        logger.info("Сообщение успешно отправлено")


def get_api_answer(current_timestamp):
    """Получение ответа с ENDPOINT."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except requests.exceptions.RequestException:
        raise GetApiAnswerError
    # если это убрать - pytest не проходит
    if homework_statuses.status_code != 200:
        raise GetApiAnswerError
    response = homework_statuses.json()
    return response


def check_response(response):
    """Проверка ответа."""
    homework = response["homeworks"]
    if isinstance(homework, dict):
        raise ValueError("homework - это словарь")
    if not isinstance(homework, list):
        raise ValueError("homework - это список")
    if not response["homeworks"]:
        raise KeyError("в словаре не имеется ключа 'homeworks'")
    if (len(response["homeworks"])) == 0:
        raise IndexError("Список в check_response пришел пустым")
    return response["homeworks"]


def parse_status(homework):
    """Получение статуса ответа."""
    if not homework["homework_name"]:
        raise KeyError("в словаре не имеется ключа 'homework_name'")
    if not homework["status"]:
        raise KeyError("в словаре не имеется ключа 'status'")
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError("Такого статуса нет")
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов."""
    if not any(
        [
            (PRACTICUM_TOKEN is None),
            (TELEGRAM_TOKEN is None),
            (TELEGRAM_CHAT_ID is None),
        ]
    ):
        return True


def main():
    """Основная логика работы бота."""
    old_message = ""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            if check_tokens() is False:
                raise TokenIsEmptyError
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            message = parse_status(homework)
            if old_message != message:
                send_message(bot, message)
            else:
                logger.debug("Отсутствие новых статусов")
            current_timestamp = int(time.time())

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.exception(error)
            if old_message != message:
                send_message(bot, message)
            old_message = message
        else:
            old_message = message
        finally:
            time.sleep(TELEGRAM_RETRY_TIME)


if __name__ == "__main__":
    main()
