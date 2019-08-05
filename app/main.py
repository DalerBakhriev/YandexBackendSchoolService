from typing import List
import pandas as pd
import numpy as np
from fastapi import FastAPI, Body, Depends, Path
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_400_BAD_REQUEST
from starlette.responses import JSONResponse, PlainTextResponse

from app.crud.citizen import get_citizens_data, insert_citizens_data, get_citizens_age_and_town
from app.db.database import get_database, DataBase
from app.db.db_utils import connect_to_postgres, close_postgres_connection
from app.models.citizen import Citizen, SomeCitizensInResponse, CitizenToUpdate, AgeStatsByTown

app = FastAPI()
app.add_event_handler("startup", connect_to_postgres)
app.add_event_handler("shutdown", close_postgres_connection)


@app.post("/imports")
async def import_citizens_data(
        *,
        citizens: List[Citizen] = Body(..., embed=True),
        db: DataBase = Depends(get_database)
):
    # Валидация консистентности родственников
    citizens_relatives = {citizen.citizen_id: set(citizen.relatives) for citizen in citizens}
    for citizen_id in citizens_relatives:
        for relative_id in citizens_relatives[citizen_id]:
            if citizen_id not in citizens_relatives[relative_id]:
                return PlainTextResponse("Relatives data is inconsistent", status_code=HTTP_400_BAD_REQUEST)

    with db.pool.acquire() as conn:
        gen_import_id = await insert_citizens_data(conn=conn, citizens=citizens)

        return JSONResponse(jsonable_encoder({"data": gen_import_id}), status_code=HTTP_201_CREATED)


@app.patch("/imports/{import_id}/citizens/{citizen_id}")
async def patch_citizens_data(
        *,
        import_id: int = Path(..., title="The ID of import to get"),
        citizen_id: int = Path(..., title="Citizen id to patch info"),
        citizen: CitizenToUpdate = Body(..., title="Citizen's data to update"),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        pass


@app.get("/imports/{import_id}/citizens", response_model=SomeCitizensInResponse)
async def get_citizens(
        *,
        import_id: int = Path(..., title="The ID of import to get"),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        citizens = await get_citizens_data(conn=conn, import_id=import_id)

        return JSONResponse(
            jsonable_encoder(SomeCitizensInResponse(citizens=citizens)),
            status_code=HTTP_200_OK
        )


@app.get("/imports/{import_id}/citizens/birthdays")
async def get_citizens_and_num_presents(
        import_id: int = Path(..., title="The ID of import to get"),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        pass


@app.get("/imports/{import_id}/towns/stat/percentile/age", response_model=List[AgeStatsByTown])
async def get_citizens_age_stats(
        import_id: int = Path(...),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        citizens_age_town = await get_citizens_age_and_town(conn=conn, import_id=import_id)
        age_percentiles = (
            citizens_age_town
                .groupby("town")
                .agg({"age": [lambda x: np.percentile(x, q=50, interpolation="linear"),
                              lambda x: np.percentile(x, q=75, interpolation="linear"),
                              lambda x: np.percentile(x, q=99, interpolation="linear")
                              ]
                      })
                .rename(columns={"<lambda_0>": "p50", "<lambda_1>": "p75", "<lambda_2>": "p99"})["age"]
                .reset_index()
        )

        age_stats_by_town: List[AgeStatsByTown] = []
        for row in age_percentiles.itertuples(index=False):
            age_stats_by_town.append(
                AgeStatsByTown(
                    town=getattr(row, "town"),
                    p50=getattr(row, "p50"),
                    p75=getattr(row, "p75"),
                    p99=getattr(row, "p99")
                )
            )

        # TODO: Make "data" header for json data
        return JSONResponse(jsonable_encoder(age_stats_by_town), status_code=HTTP_200_OK)

