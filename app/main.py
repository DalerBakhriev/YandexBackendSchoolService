import os
from typing import List

from fastapi import Body, Depends, FastAPI, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST

from app.core.config import (
    IMPORT_ENDPOINT_QUERY_BODY_EXAMPLE,
    IMPORT_ID_DESCRIPTION,
    IMPORT_RESPONSE_201_EXAMPLE,
    PATCH_ENDPOINT_QUERY_BODY_EXAMPLE,
    PATCH_RESPONSE_200_EXAMPLE,
    GET_CITIZENS_RESPONSE_200_EXAMPLE,
    GET_CITIZENS_AND_NUM_PRESENTS_RESPONSE_200_EXAMPLE,
    GET_AGE_STATS_BY_TOWN_200_EXAMPLE,
    RESET_DATABASE_RESPONSE_200_EXAMPLE
)
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
    return PlainTextResponse(str(exception), status_code=HTTP_400_BAD_REQUEST)


@app.post(
    "/imports",
    summary="Import citizens to database",
    status_code=HTTP_201_CREATED,
    responses={HTTP_201_CREATED: {"description": "Created session import ID",
                                  "content": IMPORT_RESPONSE_201_EXAMPLE},
               HTTP_400_BAD_REQUEST: {"description": "Request failed validation"}}
)
async def import_citizens_data(
        *,
        citizens_to_import: CitizensToImport = Body(
            ...,
            example=IMPORT_ENDPOINT_QUERY_BODY_EXAMPLE
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


@app.patch(
    "/imports/{import_id}/citizens/{citizen_id}",
    summary="Update citizen's data",
    response_model=Citizen,
    responses={HTTP_200_OK: {"description": "Updated citizen information",
                             "content": PATCH_RESPONSE_200_EXAMPLE},
               HTTP_400_BAD_REQUEST: {"description": "Request failed validation"}}
)
async def patch_citizens_data(
        *,
        import_id: int = Path(
            ...,
            title="The ID of import to get citizen from",
            ge=1,
            description=IMPORT_ID_DESCRIPTION
        ),
        citizen_id: int = Path(
            ...,
            title="Citizen id to patch info",
            ge=0,
            description="Unique person's id within specified import session"
        ),
        citizen: CitizenToUpdate = Body(
            ...,
            title="Citizen's data to update",
            example=PATCH_ENDPOINT_QUERY_BODY_EXAMPLE
        ),
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

    # Validate that request does not contain null values
    if None in citizen.dict(skip_defaults=True).values():
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail="Null values are not allowed")

    # Validate that at least one parameter is not empty
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


@app.get(
    "/imports/{import_id}/citizens",
    summary="Get citizens information by import id",
    response_model=SomeCitizensInResponse,
    responses={HTTP_200_OK: {"description": "Information about citizens in specified session import ID",
                             "content": GET_CITIZENS_RESPONSE_200_EXAMPLE},
               HTTP_400_BAD_REQUEST: {"description": "Requested import session ID does not exist"}}
)
async def get_citizens(
        *,
        import_id: int = Path(
            ...,
            title="The ID of import session to get citizens from",
            ge=1,
            description=IMPORT_ID_DESCRIPTION
        ),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        citizens: List[Citizen] = await get_citizens_data(conn=conn, import_id=import_id)

        return JSONResponse(
            jsonable_encoder(SomeCitizensInResponse(data=citizens)),
            status_code=HTTP_200_OK
        )


@app.get(
    "/imports/{import_id}/citizens/birthdays",
    summary="Get num presents to buy for citizens in every month",
    status_code=HTTP_200_OK,
    responses={HTTP_200_OK: {"description": "List of months with citizens and presents number they need to buy",
                             "content": GET_CITIZENS_AND_NUM_PRESENTS_RESPONSE_200_EXAMPLE},
               HTTP_400_BAD_REQUEST: {"description": "Requested import session ID does not exist"}}
)
async def get_citizens_and_num_presents(
        import_id: int = Path(
            ...,
            title="The ID of import session to get num presents from",
            ge=1,
            description=IMPORT_ID_DESCRIPTION
        ),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        num_presents_by_citizen_per_month = await get_num_presents_by_citizen_per_month(
            conn=conn,
            import_id=import_id
        )

        return JSONResponse(jsonable_encoder({"data": num_presents_by_citizen_per_month}),
                            status_code=HTTP_200_OK)


@app.get(
    "/imports/{import_id}/towns/stat/percentile/age",
    response_model=AgeStatsByTownInResponse,
    summary="Get age statistics by specified import id",
    responses={HTTP_200_OK: {"description": "Citizens' age percentiles by town within specified import ID",
                             "content": GET_AGE_STATS_BY_TOWN_200_EXAMPLE},
               HTTP_400_BAD_REQUEST: {"description": "Requested import session ID does not exist"}}
)
async def get_citizens_age_stats(
        import_id: int = Path(
            ...,
            title="The ID of import session to get age stats from",
            ge=1,
            description=IMPORT_ID_DESCRIPTION
        ),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        age_stats_by_town: List[AgeStatsByTown] = await get_citizens_age_and_town(conn=conn, import_id=import_id)
        age_stats_by_town_for_response = AgeStatsByTownInResponse(data=age_stats_by_town)

        return JSONResponse(jsonable_encoder(age_stats_by_town_for_response),
                            status_code=HTTP_200_OK)


@app.delete(
    "/reset_data",
    summary="Refresh database and import_id counter",
    responses={HTTP_200_OK: {"description": "Notification that database was reset",
                             "content": RESET_DATABASE_RESPONSE_200_EXAMPLE},
               HTTP_400_BAD_REQUEST: {"description": "Wrong admin credentials"}}
)
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
            return JSONResponse(jsonable_encoder({"data_was_reset": "ok"}),
                                status_code=HTTP_200_OK)
    else:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail="Wrong administrator credentials")
