import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator

MAX_GEO_PARAMETER_LENGTH = 256
NUMBER_OR_LETTER = re.compile("\\w")


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

    @validator("citizen_id")
    def validate_citizen_id(cls, citizen_id: int):

        if citizen_id < 0:
            raise ValueError("Citizen id is invalid")
        return citizen_id

    @validator("town", "street", "building")
    def validate_parameter_name(cls, parameter_value: str):

        if len(parameter_value) < 1:
            raise ValueError("Value is empty")

        if len(parameter_value) > MAX_GEO_PARAMETER_LENGTH:
            raise ValueError("Value is too large")

        numbers_or_letters = re.findall(NUMBER_OR_LETTER, parameter_value)
        if len(numbers_or_letters) < 1:
            raise ValueError("Number of numbers or letters is invalid")

        return parameter_value

    @validator("birth_date")
    def validate_birth_date(cls, date_value: str):

        request_date = datetime.strptime(date_value, "%d.%m.%Y")
        if request_date > datetime.utcnow():
            raise ValueError("Birth date is later than current date")
        return date_value

    @validator("gender")
    def validate_gender(cls, gender_value: str):
        if gender_value not in {"male", "female"}:
            raise ValueError("Gender is invalid")
        return gender_value

    @validator("apartment")
    def validate_apartment_num(cls, apartment_num: int):

        if apartment_num < 0:
            raise ValueError("Apartment number must be positive")
        return apartment_num

    @validator("name")
    def validate_name_length(cls, name_value: str):

        if len(name_value) < 1:
            raise ValueError("Name value is empty")

        if len(name_value) > MAX_GEO_PARAMETER_LENGTH:
            raise ValueError("Name value is too large")

        return name_value


class CitizensToImport(BaseModel):
    citizens: List[Citizen]

    @validator("citizens", whole=True)
    def validate_relatives_consistency(cls, citizens_values: List[Citizen]):
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
    apartment: Optional[int] = None
    name: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    relatives: Optional[List[int]] = None

    @validator("town", "street", "building")
    def validate_parameter_name(cls, parameter_value: str):

        if parameter_value is not None:
            if len(parameter_value) < 1:
                raise ValueError("Value is empty")

            if len(parameter_value) > MAX_GEO_PARAMETER_LENGTH:
                raise ValueError("Value is too large")

            numbers_or_letters = re.findall(NUMBER_OR_LETTER, parameter_value)
            if len(numbers_or_letters) < 1:
                raise ValueError("Number of numbers or letters is invalid")

        return parameter_value

    @validator("gender")
    def validate_gender(cls, gender_value: str):
        if gender_value is not None and gender_value not in {"male", "female"}:
            raise ValueError("Gender is invalid")
        return gender_value

    @validator("birth_date")
    def validate_birth_date_format(cls, date_value):

        if date_value is not None:
            request_date = datetime.strptime(date_value, "%d.%m.%Y")
            if request_date > datetime.utcnow():
                raise ValueError("Birth date is later than current date")
        return date_value

    @validator("apartment")
    def validate_apartment_num(cls, apartment_num: int):
        if apartment_num is not None:
            if apartment_num < 0:
                raise ValueError("Apartment number must be positive")
        return apartment_num


class SomeCitizensInResponse(BaseModel):
    data: List[Citizen]


class AgeStatsByTown(BaseModel):

    town: str
    p50: int
    p75: int
    p99: int


class AgeStatsByTownInResponse(BaseModel):
    data: List[AgeStatsByTown]
