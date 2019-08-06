from pydantic import BaseModel
from typing import List, Optional, Tuple
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


class CitizenInResponse(BaseModel):
    data: Citizen


class CitizenToUpdate(BaseModel):

    town: Optional[str] = None
    street: Optional[str] = None
    building: Optional[str] = None
    apartment: Optional[str] = None
    name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    relatives: Optional[List[int]] = None


class SomeCitizensInResponse(BaseModel):
    data: List[Citizen]


class AgeStatsByTown(BaseModel):

    town: str
    p50: int
    p75: int
    p99: int


class AgeStatsByTownInResponse(BaseModel):
    data: List[AgeStatsByTown]

