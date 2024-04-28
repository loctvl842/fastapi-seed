from sqlalchemy import Column, Integer, String

from core.db import Base
from core.db.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
