from datetime import datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
