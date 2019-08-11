from typing import List, Optional

from pydantic import BaseModel


class Citizen(BaseModel):

    citizen_id: int
    town: str
    street: str
    building: str
    apartment: int
    name: str
    birth_date: str
    gender: str
    relatives: List[int]


class CitizensToImport(BaseModel):
    citizens: List[Citizen]


class CitizenInResponse(BaseModel):
    data: Citizen


class CitizenToUpdate(BaseModel):

    town: Optional[str] = None
    street: Optional[str] = None
    building: Optional[str] = None
    apartment: Optional[str] = None
    name: Optional[str] = None
    birth_date: Optional[str] = None
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
