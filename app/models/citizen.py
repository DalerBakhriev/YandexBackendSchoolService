from pydantic import BaseModel
from typing import List
from datetime import date


class Citizen(BaseModel):

    citizen_id: int
    town: str
    street: str
    building: str
    apartment: int
    name: str
    birth_date: date
    gender: str
    relatives: List[int] = []
