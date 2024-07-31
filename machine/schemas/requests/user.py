from typing import Optional
from pydantic import BaseModel


class UserRequest(BaseModel):
    id: Optional[int]
    name: str
