from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import numpy as np
from asyncpg import Connection
from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError
from starlette.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from app.models.citizen import AgeStatsByTown, Citizen, CitizenToUpdate


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
            (generated_import_id, citizen.citizen_id, citizen.town,
             citizen.street, citizen.building, citizen.apartment,
             citizen.name, datetime.strptime(citizen.birth_date, "%d.%m.%Y"), citizen.gender)
            for citizen in citizens
        ]

        try:
            _ = await conn.copy_records_to_table(
                table_name="citizens",
                records=citizens_records,
                columns=["import_id", "citizen_id", "town", "street", "building",
                         "apartment", "name", "birth_date", "gender"],
                schema_name="public"
            )
        except UniqueViolationError:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                detail="Citizen id is not unique")

        citizen_relatives = list()
        for citizen in citizens:
            for relative_id in citizen.relatives:
                citizen_relatives.append((generated_import_id, citizen.citizen_id, relative_id))

        try:
            _ = await conn.copy_records_to_table(
                table_name="relatives",
                records=citizen_relatives,
                columns=["import_id", "citizen_id", "relative_id"],
                schema_name="public"
            )
        except UniqueViolationError:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                detail="Detected duplicated relative_id")
        except ForeignKeyViolationError:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                detail="Detected nonexistent relative_id")

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
        FROM public.citizens citizens LEFT JOIN public.relatives relatives_
        ON citizens.import_id = relatives_.import_id AND citizens.citizen_id = relatives_.citizen_id
        WHERE citizens.import_id = $1 AND citizens.citizen_id = $2
        GROUP BY town, street, building, apartment, name, birth_date, gender
        """,
        import_id,
        citizen_id
    )

    if citizen_row is None:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=f"Citizen with id = {citizen_id} is not presented in import id: {import_id}")
    citizen = Citizen(
        citizen_id=citizen_id,
        town=citizen_row["town"],
        street=citizen_row["street"],
        building=citizen_row["building"],
        apartment=citizen_row["apartment"],
        name=citizen_row["name"],
        birth_date=citizen_row["birth_date"].strftime("%d.%m.%Y"),
        gender=citizen_row["gender"],
        relatives=citizen_row["relatives"] if citizen_row["relatives"][0] is not None else []
    )

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

    # Update basic citizens information
    citizen_from_db.town = citizen.town if citizen.town else citizen_from_db.town
    citizen_from_db.street = citizen.street if citizen.street else citizen_from_db.street
    citizen_from_db.building = citizen.building if citizen.building else citizen_from_db.building
    citizen_from_db.apartment = citizen.apartment if citizen.apartment else citizen_from_db.apartment
    citizen_from_db.name = citizen.name if citizen.name else citizen_from_db.name
    citizen_from_db.gender = citizen.gender if citizen.gender else citizen_from_db.gender

    citizen_from_db.birth_date = datetime.strptime(
        citizen.birth_date,
        "%d.%m.%Y"
    ) if citizen.birth_date else datetime.strptime(citizen_from_db.birth_date, "%d.%m.%Y")

    async with conn.transaction():

        await conn.execute(
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
            citizen_from_db.gender,
            import_id,
            citizen_id
        )

        # Relative information update
        if citizen.relatives is not None:
            await conn.execute(
                """
                DELETE
                FROM public.relatives
                WHERE (import_id = $1 AND citizen_id = $2)
                      OR
                      (import_id = $1 AND relative_id = $2)
                """,
                import_id,
                citizen_id
            )

            if citizen.relatives:
                update_for_relatives = list()

                for relative_id in citizen.relatives:

                    if relative_id == citizen_id:
                        update_for_relatives.append((import_id, citizen_id, relative_id))
                    else:
                        update_for_relatives.extend(
                            [(import_id, citizen_id, relative_id),
                             (import_id, relative_id, citizen_id)]
                        )

                try:
                    _ = await conn.copy_records_to_table(
                        table_name="relatives",
                        records=update_for_relatives,
                        columns=["import_id", "citizen_id", "relative_id"],
                        schema_name="public"
                    )
                except ForeignKeyViolationError:
                    raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                        detail=f"Found nonexistent relative import id = {import_id}")
                except UniqueViolationError:
                    raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                                        detail="Detected duplicated relative_id")

            citizen_from_db.relatives = citizen.relatives
        citizen_from_db.birth_date = citizen_from_db.birth_date.strftime("%d.%m.%Y")

        return citizen_from_db


async def get_citizens_data(conn: Connection, import_id: int) -> List[Citizen]:

    """
    Возвращает список всех жителей для указанного набора данных.
    :param conn: asyncpg connection
    :param import_id: id of upload from provider
    :return: Citizens data with chosen import_id
    """

    citizens: List[Citizen] = list()
    citizens_rows = await conn.fetch(
        """
        SELECT citizens.citizen_id AS citizen_id_,
               town,
               street,
               building,
               apartment,
               name,
               birth_date,
               gender,
               array_agg(relative_id) relatives
        FROM public.citizens citizens LEFT JOIN public.relatives relatives_
        ON citizens.import_id = relatives_.import_id AND citizens.citizen_id = relatives_.citizen_id
        WHERE citizens.import_id = $1
        GROUP BY (citizens.citizen_id, town, street, building, apartment, name, birth_date, gender)
        """,
        import_id
    )
    if len(citizens_rows) == 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=f"There is no data with import id = {import_id}")
    for citizen_row in citizens_rows:
        citizens.append(Citizen(
            citizen_id=citizen_row["citizen_id_"],
            town=citizen_row["town"],
            street=citizen_row["street"],
            building=citizen_row["building"],
            apartment=citizen_row["apartment"],
            name=citizen_row["name"],
            birth_date=citizen_row["birth_date"].strftime("%d.%m.%Y"),
            gender=citizen_row["gender"],
            relatives=citizen_row["relatives"] if citizen_row["relatives"][0] is not None else []
    ))

    return citizens


async def get_num_presents_by_citizen_per_month(conn: Connection, import_id: int) -> Dict[int, List[Dict[int, int]]]:
    """
    Возвращает жителей и количество подарков, которые они должны покупать помесячно
    :param conn: asyncpg connection
    :param import_id: id of upload from provider
    :return: number of presents for every user per month
    """

    num_presents_by_citizen_per_month_rows = await conn.fetch(
        """
        SELECT citizen_id_, month, COUNT(DISTINCT relative_id) num_birthdays
        FROM
            (SELECT citizens.citizen_id AS relative_id,
                    relatives.relative_id AS citizen_id_,
                    EXTRACT(MONTH from birth_date)::integer AS month
            FROM public.citizens citizens LEFT JOIN public.relatives relatives
            ON citizens.citizen_id = relatives.citizen_id AND citizens.import_id = relatives.import_id
            WHERE citizens.import_id = $1) subquery
        GROUP BY citizen_id_, month
        """,
        import_id
    )

    if len(num_presents_by_citizen_per_month_rows) == 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=f"There is no data with import id = {import_id}")

    num_presents_by_citizen_per_month = defaultdict(list)
    for row in num_presents_by_citizen_per_month_rows:
        if row["citizen_id_"] is not None:
            num_presents_by_citizen_per_month[str(row["month"])].append(
                {"citizen_id": row["citizen_id_"],
                 "presents": row["num_birthdays"]}
            )

    num_presents_by_citizen_per_month = dict(num_presents_by_citizen_per_month)
    for month_num in map(str, range(1, 12 + 1)):
        if month_num not in num_presents_by_citizen_per_month:
            num_presents_by_citizen_per_month[month_num] = list()

    return num_presents_by_citizen_per_month


async def get_citizens_age_and_town(conn: Connection, import_id: int) -> List[AgeStatsByTown]:

    """
    Returns age stats (50, 75 and 99 percentile) by town in selected import_id
    :param conn: asyncpg connection
    :param import_id: id of upload from provider
    :return: age statistics by town
    """

    citizens_age_and_town = await conn.fetch(
        """
        SELECT EXTRACT(YEAR from age(timezone('utc', now()), birth_date)) age, town
        FROM public.citizens
        WHERE import_id = $1
        """,
        import_id
    )

    if len(citizens_age_and_town) == 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=f"There is no data with import id = {import_id}")
    ages_by_town = defaultdict(list)
    for age_as_string, town in citizens_age_and_town:
        ages_by_town[town].append(int(age_as_string))

    age_stats_by_town: List[AgeStatsByTown] = list()

    for town in ages_by_town:
        age_stats_by_town.append(
            AgeStatsByTown(
                town=town,
                p50=float(round(np.percentile(ages_by_town[town], q=50, interpolation="linear"), 2)),
                p75=float(round(np.percentile(ages_by_town[town], q=75, interpolation="linear"), 2)),
                p99=float(round(np.percentile(ages_by_town[town], q=99, interpolation="linear"), 2))
            )
        )

    return age_stats_by_town


async def clear_db(conn: Connection) -> None:
    """
    Clears database and resets sequence counter for import_id to 1
    :param conn: asyncpg connection
    :return:
    """

    async with conn.transaction():

        await conn.execute(
            """
            DELETE
            FROM public.relatives
            """
        )

        await conn.execute(
            """
            DELETE
            FROM public.citizens
            """
        )

        await conn.execute(
            """
            ALTER SEQUENCE imports_seq RESTART WITH 1;
            """
        )
