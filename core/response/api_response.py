from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Ok(BaseModel, Generic[T]):
    status: str = "success"
    data: T

    def __init__(self, data: T):
        super().__init__(data=data)

    @staticmethod
    def format(data):
        return {"status": "success", "data": data}


class ErrorInfo(BaseModel):
    error_code: int
    message: str


class Error(BaseModel):
    status: str = "error"
    error: ErrorInfo

    def __init__(self, error_code: int, message: str):
        super().__init__(error=ErrorInfo(error_code=error_code, message=message))
