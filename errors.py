from http import HTTPStatus


class AppError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code
        self.message = message


class ClientAlreadyRunning(AppError):
    def __init__(self):
        super().__init__("There is already a client running", HTTPStatus.CONFLICT)


class NoClientRunning(AppError):
    def __init__(self):
        super().__init__("There is no client currently running", HTTPStatus.NOT_FOUND)


class BadConfig(AppError):
    def __init__(self):
        super().__init__("Bad configuration", HTTPStatus.BAD_REQUEST)