from pydantic import BaseModel
from typing import List, Tuple
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


class CitizenToUpdate(BaseModel):

    town: str = None
    street: str = None
    building: str = None
    apartment: str = None
    name: str = None
    birth_date: date = None
    gender: str = None
    relatives: List[int] = None


class SomeCitizensInResponse(BaseModel):
    citizens: List[Citizen]


class AgeStatsByTown(BaseModel):

    town: str
    p50: int
    p75: int
    p99: int

