from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator


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

    @validator("birth_date")
    def validate_birth_date_format(cls, date_value: str):

        datetime.strptime(date_value, "%d.%m.%Y")
        return date_value

    @validator("gender")
    def validate_gender(cls, gender_value: str):
        if gender_value not in {"male", "female"}:
            raise ValueError("Gender is invalid")
        return gender_value


class CitizensToImport(BaseModel):
    citizens: List[Citizen]

    @validator("citizens", whole=True)
    def validate_relatives_consistency(cls, citizens_values: List[Citizen]):
        print(citizens_values)
        citizens_relatives = {citizen.citizen_id: set(citizen.relatives) for citizen in citizens_values}
        for citizen_id in citizens_relatives:
            for relative_id in citizens_relatives[citizen_id]:
                if citizen_id not in citizens_relatives.get(relative_id, set()):
                    raise ValueError("Relatives data is inconsistent")
        return citizens_values


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

    @validator("gender")
    def validate_gender(cls, gender_value: str):
        if gender_value is not None and gender_value not in {"male", "female"}:
            raise ValueError("Gender is invalid")
        return gender_value

    @validator("birth_date")
    def validate_birth_date_format(cls, date_value):

        if date_value is not None:
            datetime.strptime(date_value, "%d.%m.%Y")

        return date_value


class SomeCitizensInResponse(BaseModel):
    data: List[Citizen]


class AgeStatsByTown(BaseModel):

    town: str
    p50: int
    p75: int
    p99: int


class AgeStatsByTownInResponse(BaseModel):
    data: List[AgeStatsByTown]
