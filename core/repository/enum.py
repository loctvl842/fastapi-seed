from pydantic import BaseModel


class SynchronizeSessionEnum(BaseModel):
    FETCH: str = "fetch"
    EVALUATE: str = "evaluate"
    FALSE: bool = False
