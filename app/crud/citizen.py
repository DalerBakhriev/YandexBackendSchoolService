from typing import List
from collections import defaultdict
from app.models.citizen import AgeStatsByTown, Citizen, CitizenToUpdate
from asyncpg import Connection
import numpy as np


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


async def get_citizen(conn: Connection, import_id: int, citizen_id: int) -> Citizen:
    """
    Вовзращает из базы информаицю о гражданине по import_id и citizen_id
    :param conn: asyncpg connection
    :param import_id: id of upload from provider
    :param citizen_id: citizen id of citizen to update
    :return: citizen information
    """
    citizen_row = await conn.fetchrow(
        """
        SELECT town,
               street,
               building,
               apartment,
               name,
               birth_date,
               gender,
               array_agg(relative_id) relatives
        FROM public.citizens citizens JOIN public.relatives relatives_
        ON citizens.import_id = relatives_.import_id AND citizens.citizen_id = relatives_.citizen_id
        WHERE citizens.import_id = $1 AND citizens.citizen_id = $2
        """,
        import_id,
        citizen_id
    )
    citizen = Citizen(**citizen_row)

    return citizen


async def update_citizens_data(
        conn: Connection,
        import_id: int,
        citizen_id: int,
        citizen: CitizenToUpdate
) -> Citizen:
    """
    Обновляет в базе информацию о гражданине, возвращает обновленную информацию.
    :param conn: asyncpg connection to database
    :param import_id: id of upload from provider
    :param citizen_id: citizen_id of citizen to update
    :param citizen: citizen data to for updating
    :return: Updated citizen information
    """
    citizen_from_db: Citizen = await get_citizen(
        conn=conn,
        import_id=import_id,
        citizen_id=citizen_id
    )

    # Обновление основной информации о жителях
    citizen_from_db.town = citizen.town if citizen.town else citizen_from_db.town
    citizen_from_db.street = citizen.street if citizen.street else citizen_from_db.street
    citizen_from_db.building = citizen.building if citizen.building else citizen_from_db.building
    citizen_from_db.apartment = citizen.apartment if citizen.apartment else citizen_from_db.apartment
    citizen_from_db.name = citizen.name if citizen.name else citizen_from_db.name
    citizen_from_db.birth_date = citizen.birth_date if citizen.birth_date else citizen_from_db.birth_date
    citizen_from_db.gender = citizen.gender if citizen.gender else citizen_from_db.gender

    _ = await conn.fetchrow(
        """
        UPDATE public.citizens
        SET town = $1,
            street = $2,
            building = $3,
            apartment = $4,
            name = $5,
            birth_date = $6,
            gender = $7
        WHERE import_id = $8 AND citizen_id = $9
        """,
        citizen_from_db.town,
        citizen_from_db.street,
        citizen_from_db.building,
        citizen_from_db.apartment,
        citizen_from_db.name,
        citizen_from_db.birth_date,
        citizen_from_db.gender
    )

    # Обновление информации о родственниках
    if citizen.relatives is not None:
        await conn.execute(
            """
            DELETE
            FROM public.relatives
            WHERE import_id = $1 AND citizen_id = $2
            """,
            import_id,
            citizen_id
        )

        if citizen.relatives:
            update_for_relatives = []

            for relative_id in citizen.relatives:
                update_for_relatives.extend(
                    [(import_id, citizen_id, relative_id),
                     (import_id, relative_id, citizen_id)]
                )
            _ = await conn.copy_records_to_table(
                table_name="relatives",
                records=update_for_relatives,
                columns=["import_id", "citizen_id", "relative_id"],
                schema_name="public"
            )
        citizen_from_db.relatives = citizen.relatives

    return citizen_from_db


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
        SELECT citizen_id,
               town,
               street,
               building,
               apartment,
               name,
               birth_date,
               gender,
               array_agg(relative_id) relatives
        FROM public.citizens citizens JOIN public.relatives relatives_
        ON  citizens.import_id = relatives_.import_id AND citizens.citizen_id = relatives_.citizen_id
        WHERE citizens.import_id = $1
        GROUP BY (citizen_id, town, street, building, apartment, name, birth_date, gender)
        """,
        import_id
    )
    for citizen_row in citizens_rows:
        citizens.append(Citizen(**citizen_row))

    return citizens


async def get_citizens_age_and_town(conn: Connection, import_id: int) -> List[AgeStatsByTown]:

    """
    Returns age stats (50, 75 and 99 percentile) by town in selected import_id
    :param conn: asyncpg connection
    :param import_id: id of upload from provider
    :return: age statistics by town
    """

    citizens_age_and_town = await conn.fetch(
        """
        SELECT age(birth_date) age, town
        FROM public.citizens
        WHERE import_id = $1
        """,
        import_id
    )
    ages_by_town = defaultdict(list)
    for age_as_string, town in citizens_age_and_town:
        ages_by_town[town].append(int(age_as_string.split(" ")[0]))

    age_stats_by_town: List[AgeStatsByTown] = []

    for town in ages_by_town:
        age_stats_by_town.append(
            AgeStatsByTown(
                town=town,
                p50=np.percentile(ages_by_town[town], q=50, interpolation="linear"),
                p75=np.percentile(ages_by_town[town], q=75, interpolation="linear"),
                p99=np.percentile(ages_by_town[town], q=99, interpolation="linear")
            )
        )

    return age_stats_by_town
