class NoMessageSendError(Exception):
    """В send_message бот сообщение не отправил."""

    def __init__(self, message="В send_message бот сообщение не отправил"):
        self.message = message
        super().__init__(self.message)


class GetApiAnswerError(Exception):
    """Endpoint не отвечает."""

    def __init__(self, message="Endpoint не отвечает"):
        self.message = message
        super().__init__(self.message)


class TokenIsEmptyError(Exception):
    """Есть пустые токены"."""

    def __init__(self, message="Есть пустые токены"):
        self.message = message
        super().__init__(self.message)
