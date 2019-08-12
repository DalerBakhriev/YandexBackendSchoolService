from fastapi import Body, Depends, FastAPI, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.responses import RedirectResponse
from starlette.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST

from app.crud.citizen import (
    get_citizens_data,
    insert_citizens_data,
    get_citizens_age_and_town,
    update_citizens_data,
    get_num_presents_by_citizen_per_month
)
from app.db.database import get_database, DataBase
from app.db.db_utils import connect_to_postgres, close_postgres_connection
from app.models.citizen import (
    AgeStatsByTownInResponse,
    Citizen,
    CitizensToImport,
    CitizenInResponse,
    CitizenToUpdate,
    SomeCitizensInResponse
)

app = FastAPI()
app.add_event_handler("startup", connect_to_postgres)
app.add_event_handler("shutdown", close_postgres_connection)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: Exception):
    return PlainTextResponse(str(exception), status_code=400)


@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.post("/imports")
async def import_citizens_data(
        *,
        citizens_to_import: CitizensToImport = Body(...),
        db: DataBase = Depends(get_database)
):

    citizens = citizens_to_import.citizens

    async with db.pool.acquire() as conn:

        gen_import_id = await insert_citizens_data(conn=conn, citizens=citizens)
        return JSONResponse(jsonable_encoder({"data": gen_import_id}),
                            status_code=HTTP_201_CREATED)


@app.patch("/imports/{import_id}/citizens/{citizen_id}", response_model=Citizen)
async def patch_citizens_data(
        *,
        import_id: int = Path(..., title="The ID of import to get", ge=1),
        citizen_id: int = Path(..., title="Citizen id to patch info"),
        citizen: CitizenToUpdate = Body(..., title="Citizen's data to update"),
        db: DataBase = Depends(get_database)
):
    # Валидируем, что хотя бы один параметр не пустой
    num_parameters_to_update = sum([
        param_value is not None for param_value in citizen.dict().values()
    ])

    if num_parameters_to_update == 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail="There are no parameters to update")

    # TODO: Валидация на существующие citizen_id в списке родственников
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


@app.get("/imports/{import_id}/citizens", response_model=SomeCitizensInResponse)
async def get_citizens(
        *,
        import_id: int = Path(..., title="The ID of import to get", ge=1),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        citizens = await get_citizens_data(conn=conn, import_id=import_id)

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
        age_stats_by_town = await get_citizens_age_and_town(conn=conn, import_id=import_id)
        age_stats_by_town_for_response = AgeStatsByTownInResponse(data=age_stats_by_town)

        return JSONResponse(jsonable_encoder(age_stats_by_town_for_response),
                            status_code=HTTP_200_OK)

