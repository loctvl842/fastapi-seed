from http import HTTPStatus

from typing import Any, Optional


class APIException(Exception):
    code = HTTPStatus.BAD_GATEWAY
    error_code = HTTPStatus.BAD_GATEWAY
    message = HTTPStatus.BAD_GATEWAY.description
    detail: Optional[Any] = None
    headers: Optional[Any] = None

    def __init__(self, message=None, detail=None, headers=None):
        self.message = message or self.message
        self.detail = detail
        self.headers = headers
        super().__init__(self.message)

    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message}, detail={self.detail})"


class RateLimitException(APIException):
    code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = HTTPStatus.TOO_MANY_REQUESTS
    message = HTTPStatus.TOO_MANY_REQUESTS.description


class NotImplementedException(APIException):
    code = HTTPStatus.NOT_IMPLEMENTED
    error_code = HTTPStatus.NOT_IMPLEMENTED
    message = HTTPStatus.NOT_IMPLEMENTED.description


class ApplicationException(APIException):
    code = HTTPStatus.BAD_REQUEST
    error_code = HTTPStatus.BAD_REQUEST
    message = HTTPStatus.BAD_REQUEST.description


class UnauthorizedException(APIException):
    code = HTTPStatus.UNAUTHORIZED
    error_code = HTTPStatus.UNAUTHORIZED
    message = HTTPStatus.UNAUTHORIZED.description


class UnprocessableEntityException(APIException):
    code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message = HTTPStatus.UNPROCESSABLE_ENTITY.description


class ForbiddenException(APIException):
    code = HTTPStatus.FORBIDDEN
    error_code = HTTPStatus.FORBIDDEN
    message = HTTPStatus.FORBIDDEN.description


class BadRequestException(APIException):
    code = HTTPStatus.BAD_REQUEST
    error_code = HTTPStatus.BAD_REQUEST
    message = HTTPStatus.BAD_REQUEST.description


class NotFoundException(APIException):
    code = HTTPStatus.NOT_FOUND
    error_code = HTTPStatus.NOT_FOUND
    message = HTTPStatus.NOT_FOUND.description


class SystemException(APIException):
    code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = HTTPStatus.INTERNAL_SERVER_ERROR
    message = HTTPStatus.INTERNAL_SERVER_ERROR.description


class PermissionException(APIException):
    code = HTTPStatus.FORBIDDEN
    error_code = HTTPStatus.FORBIDDEN
    message = "Permission error: You do not have the necessary permissions."

    def __init__(self, message=None, detail=None, headers=None):
        super().__init__(message or self.message, detail, headers)
