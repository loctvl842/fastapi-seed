from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Ok(BaseModel, Generic[T]):
    status: str = "success"
    data: T

    def __init__(self, data: T, *, status: str = "success"):
        assert status == "success"
        super().__init__(status="success", data=data)

    @staticmethod
    def format(data):
        return {"status": "success", "data": data}


class Pagination(BaseModel, Generic[T]):
    list: list[T]
    offset: int
    limit: Optional[int] = None
    total: Optional[int] = None


class ErrorInfo(BaseModel):
    error_code: int
    message: str
    detail: Optional[Any]


class Error(BaseModel):
    status: str = "error"
    error: ErrorInfo

    def __init__(self, error_code: int, message: str, detail: Optional[Any] = None, *, status: str = "error"):
        assert status == "error"
        super().__init__(error=ErrorInfo(error_code=error_code, message=message, detail=detail))
