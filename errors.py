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
        super().__init__("There is no client currently running or the current client is not available.", HTTPStatus.NOT_FOUND)


class WrongBodyFormat(AppError):
    def __init__(self, attributes):
        super().__init__(f"Bad body format. Expected: {attributes} attributes.", HTTPStatus.BAD_REQUEST)


class NegativeContainerNumber(AppError):
    def __init__(self, n):
        super().__init__(f"Expected a positive number of containers, but got {n}", HTTPStatus.BAD_REQUEST)


class NumericValue(AppError):
    def __init__(self, name):
        super().__init__(f"{name} must be of a numeric type")