from http import HTTPStatus


class AppError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code
        self.message = message

class ClientNotInitialized(AppError):
    def __init__(self):
        super().__init__("Client not fully initialized, try again", HTTPStatus.SERVICE_UNAVAILABLE)


class ClientAlreadyRunning(AppError):
    def __init__(self):
        super().__init__("There is already a client running", HTTPStatus.CONFLICT)


class ClientNotInstantiated(AppError):
    def __init__(self):
        super().__init__("There is no client instantiated", HTTPStatus.NOT_FOUND)


class ClientNotAvailable(AppError):
    def __init__(self):
        super().__init__("Client not available, try again later", HTTPStatus.SERVICE_UNAVAILABLE)


class WrongBodyFormat(AppError):
    def __init__(self, attributes):
        super().__init__(f"Bad body format. Expected: {attributes} attributes.", HTTPStatus.BAD_REQUEST)


class NegativeContainerNumber(AppError):
    def __init__(self, n):
        super().__init__(f"Expected a positive number of containers, but got {n}", HTTPStatus.BAD_REQUEST)


class NumericValue(AppError):
    def __init__(self, name):
        super().__init__(f"{name} must be of a numeric type")