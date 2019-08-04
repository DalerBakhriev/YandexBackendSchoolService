from typing import List

from fastapi import FastAPI, Body, Depends, Path
from starlette.status import HTTP_201_CREATED

from app.db.database import get_database, DataBase
from app.db.db_utils import connect_to_postgres, close_postgres_connection
from app.models.citizen import Citizen

app = FastAPI()
app.add_event_handler("startup", connect_to_postgres)
app.add_event_handler("shutdown", close_postgres_connection)


@app.post("/imports", status_code=HTTP_201_CREATED)
async def import_citizens_data(
        *,
        citizens: List[Citizen] = Body(..., embed=True),
        db: DataBase = Depends(get_database)
):
    with db.pool.acquire() as conn:
        pass


@app.patch("/imports/{import_id}/citizens/{citizen_id}")
async def patch_citizens_data(
        *,
        import_id: int = Path(..., title="The ID of import to get"),
        citizen_id: int = Path(..., title="Citizen id to patch info"),
        citizens: Citizen = Body(...),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        pass


@app.get("/imports/{import_id}/citizens")
async def get_citizens(
        *,
        import_id: int = Path(..., title="The ID of import go get"),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        pass


@app.get("/imports/{import_id}/citizens/birthdays")
async def get_citizens_and_num_gifts(
        import_id: int = Path(..., title="The ID of import go get"),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        pass


@app.get("/imports/{import_id}/towns/stat/percentile/age")
async def get_citizens_age_stats(
        import_id: int = Path(...),
        db: DataBase = Depends(get_database)
):
    async with db.pool.acquire() as conn:
        pass
