import os
from typing import List

from fastapi import Body, Depends, FastAPI, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST

from app.crud.citizen import (
    get_citizens_data,
    insert_citizens_data,
    get_citizens_age_and_town,
    update_citizens_data,
    get_num_presents_by_citizen_per_month,
    clear_db
)
from app.db.database import get_database, DataBase
from app.db.db_utils import connect_to_postgres, close_postgres_connection
from app.models.citizen import (
    AdminCredentials,
    AgeStatsByTown,
    AgeStatsByTownInResponse,
    Citizen,
    CitizensToImport,
    CitizenInResponse,
    CitizenToUpdate,
    SomeCitizensInResponse
)

app = FastAPI(
    docs_url="/",
    title="Yandex backend school service",
    description="REST API service as entrance test in Yandex backend school"
)
app.add_event_handler("startup", connect_to_postgres)
app.add_event_handler("shutdown", close_postgres_connection)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: Exception):
    return PlainTextResponse(str(exception), status_code=400)


@app.post("/imports",
          summary="Import citizens to database",
          response_description="Generated import id for upload session")
async def import_citizens_data(
        *,
        citizens_to_import: CitizensToImport = Body(
            ...,
            example={"citizens": [
                {
                    "citizen_id": 1,
                    "town": "Москва",
                    "street": "Бассейная",
                    "building": "дом Колотушкина",
                    "apartment": 666,
                    "name": "Рассеяный",
                    "birth_date": "23.11.2001",
                    "gender": "male",
                    "relatives": []
                }
            ]}
        ),
        db: DataBase = Depends(get_database)
):
    """
    Imports information about citizens in database

    - **citizen_id**: unique person's id within current upload session
    - **town**: town where person lives (not empty string, max length is 256, at least 1 number or letter)
    - **street**: street on which person lives (not empty, max length is 256, at least 1 number or letter)
    - **building**: building identifier where person lives (not empty, max length is 256, at least 1 number or letter)
    - **apartment**: number of apartment where person lives (must be greater or equals 0)
    - **name**: person's name (at least 1 number or letter)
    - **birth_date**: person's birth date (format: 'dd.mm.YY', must be earlier than current date)
    - **gender**: person's gender
    - **relatives**: list of person's relatives' citizen ids (if A is B's relative then B is A's relative)
    """

    citizens = citizens_to_import.citizens

    async with db.pool.acquire() as conn:

        gen_import_id: int = await insert_citizens_data(conn=conn, citizens=citizens)
        return JSONResponse(jsonable_encoder({"data": {"import_id": gen_import_id}}),
                            status_code=HTTP_201_CREATED)


@app.patch("/imports/{import_id}/citizens/{citizen_id}",
           summary="Update citizen's data",
           response_model=Citizen,
           response_description="All information about updated citizen")
async def patch_citizens_data(
        *,
        import_id: int = Path(..., title="The ID of import to get", ge=1),
        citizen_id: int = Path(..., title="Citizen id to patch info", ge=0),
        citizen: CitizenToUpdate = Body(
            ...,
            title="Citizen's data to update",
            example={
                "name": "Рассеяная",
                "gender": "female"
            }),
        db: DataBase = Depends(get_database)
):
    """
    Updates information about one citizen

    - **town**: town where person lives (not empty string, max length is 256, at least 1 number or letter)
    - **street**: street on which person lives (not empty, max length is 256, at least 1 number or letter)
    - **building**: building identifier where person lives (not empty, max length is 256, at least 1 number or letter)
    - **apartment**: number of apartment where person lives (must be greater or equals 0)
    - **name**: person's name (at least 1 number or letter)
    - **birth_date**: person's birth date (format: 'dd.mm.YY', must be earlier than current date)
    - **gender**: person's gender
    - **relatives**: list of person's relatives' citizen ids (if A is B's relative then B is A's relative)
    """

    # Валидируем, что в запросе не было значений null
    if None in citizen.dict(skip_defaults=True).values():
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail="Null values are not allowed")

    # Валидируем, что хотя бы один параметр не пустой
    num_parameters_to_update = sum([
        param_value is not None for param_value in citizen.dict().values()
    ])

    if num_parameters_to_update == 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail="There are no parameters to update")

    async with db.pool.acquire() as conn:

        updated_citizen: Citizen = await update_citizens_data(
            conn=conn,
            import_id=import_id,
            citizen_id=citizen_id,
            citizen=citizen
        )

        updated_citizen_for_response = CitizenInResponse(data=updated_citizen)
        return JSONResponse(jsonable_encoder(updated_citizen_for_response),
                            status_code=HTTP_200_OK)


@app.get("/imports/{import_id}/citizens",
         summary="Get citizens information by import id",
         response_model=SomeCitizensInResponse,
         response_description="All information about citizens with specified import id")
async def get_citizens(
        *,
        import_id: int = Path(..., title="The ID of import to get", ge=1),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        citizens: List[Citizen] = await get_citizens_data(conn=conn, import_id=import_id)

        return JSONResponse(
            jsonable_encoder(SomeCitizensInResponse(data=citizens)),
            status_code=HTTP_200_OK
        )


@app.get("/imports/{import_id}/citizens/birthdays")
async def get_citizens_and_num_presents(
        import_id: int = Path(..., title="The ID of import to get", ge=1),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        num_presents_by_citizen_per_month = await get_num_presents_by_citizen_per_month(
            conn=conn,
            import_id=import_id
        )

        return JSONResponse(jsonable_encoder({"data": num_presents_by_citizen_per_month}),
                            status_code=HTTP_200_OK)


@app.get("/imports/{import_id}/towns/stat/percentile/age", response_model=AgeStatsByTownInResponse)
async def get_citizens_age_stats(
        import_id: int = Path(..., title="The ID of import to get", ge=1),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        age_stats_by_town: List[AgeStatsByTown] = await get_citizens_age_and_town(conn=conn, import_id=import_id)
        age_stats_by_town_for_response = AgeStatsByTownInResponse(data=age_stats_by_town)

        return JSONResponse(jsonable_encoder(age_stats_by_town_for_response),
                            status_code=HTTP_200_OK)


@app.delete("/reset_data",
            summary="Refresh database and import_id counter",
            response_description="Sends notification that database was reset")
async def reset_data(
        *,
        admin_credentials: AdminCredentials = Body(
            ...,
            title="Admin credentials for resetting data",
            example={
                "admin_login": "Are you sure?!",
                "admin_password": "Think about it one more time!!!"
            }
        ),
        db: DataBase = Depends(get_database)
):
    """
    Be careful!!! This is endpoint for internal purposes (refreshing database after tests).
    Requires admin credentials.

    - **admin_login**: administrator login
    - **admin_password**: administrator password
    """

    required_login = os.getenv("ADMIN_LOGIN", "")
    required_password = os.getenv("ADMIN_PASSWORD", "")
    if admin_credentials.admin_login == required_login and admin_credentials.admin_password == required_password:
        async with db.pool.acquire() as conn:
            await clear_db(conn=conn)
            return JSONResponse(jsonable_encoder({"data_was_reset": "ok"}))
    else:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail="Wrong secret token")