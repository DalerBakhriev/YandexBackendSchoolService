from typing import List
from app.models.citizen import Citizen, AgeStatsByTown
from asyncpg import Connection
import numpy as np
import pandas as pd


async def insert_citizens_data(conn: Connection, citizens: List[Citizen]) -> int:
    """
    Добавляет в базу данных информацию по гражданам
    :param conn: asyncpg connection
    :param citizens: citizens to add info about
    :return:
    """

    async with conn.transaction():

        generated_import_id = await conn.fetchval("SELECT nextval('imports_seq')")
        citizens_records = [
            (generated_import_id, citizen.citizen_id, citizen.town, citizen.street, citizen.building,
             citizen.apartment, citizen.name, citizen.birth_date, citizen.gender)
            for citizen in citizens
        ]

        _ = await conn.copy_records_to_table(
            table_name="citizens",
            records=citizens_records,
            columns=["import_id", "citizen_id", "town", "street", "building",
                     "apartment", "name", "birth_date", "gender"],
            schema_name="public"
        )

        citizen_relatives = []
        for citizen in citizens:
            for relative in citizen.relatives:
                citizen_relatives.append((generated_import_id, citizen, relative))

        _ = await conn.copy_records_to_table(
            table_name="relatives",
            records=citizen_relatives,
            columns=["import_id", "citizen_id", "relative_id"],
            schema_name="public"
        )

        return generated_import_id


async def update_citizens_data(conn: Connection, import_id: int, citizen_id: int) -> Citizen:
    """
    Обновляет в базе информацию о гражданине, возвращает обновленную информацию.
    :param conn: asyncpg connection to database
    :param import_id: id of upload from provider
    :param citizen_id: citizen_id of citizen to update
    :return: Updated citizen information
    """
    raise NotImplementedError


async def get_citizens_data(conn: Connection, import_id: int) -> List[Citizen]:

    """
    Возвращает список всех жителей для указанного набора данных.
    :param conn: asyncpg connection
    :param import_id: id of upload from provider
    :return: Citizens data with chosen import_id
    """

    citizens: List[Citizen] = []
    citizens_rows = await conn.fetch(
        """
        SELECT citizen_id, town, street, building, apartment, name, birth_date, gender, array_agg(relative_id) 
        FROM public.citizens citizens JOIN public.relatives relatives
        ON  citizens.import_id = relatives.import_id and citizens.citizen_id = relatives.citizen_id
        WHERE citizens.import_id = $1
        group by (citizen_id, town, street, building, apartment, name, birth_date, gender)
        """,
        import_id
    )
    for citizen_row in citizens_rows:
        citizens.append(Citizen(**citizen_row))

    return citizens


async def get_citizens_age_and_town(conn: Connection, import_id: int) -> pd.DataFrame:

    """
    Returns age stats (50, 75 and 99 percentile) by town in selected import_id
    :param conn: asyncpg connection
    :param import_id: id of upload from provider
    :return: age statistics by town
    """
    query = f"""SELECT age(birth_date) age, town
                FROM public.citizens
                WHERE import_id = {import_id}"""
    citizens_age_and_town = await pd.read_sql(query, conn)
    citizens_age_and_town["age"] = citizens_age_and_town["age"].apply(lambda x: x.split()[0]).astype(int)

    return citizens_age_and_town
