from datetime import datetime, timedelta
import json
import os
import pandas as pd

from typing import List, Type
from app.helpers.s3_file_upload import generate_s3_url, upload_file_to_s3

# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

from app.models.company import Company, company_pydantic, company_pydantic_in, company_selection_pydantic
from app.models.agency import Agency, agency_pydantic
from app.models.user import User

from tempfile import NamedTemporaryFile


router = APIRouter(
    prefix="/company",
    tags=["company"],
    responses={404: {"description": "Not found"}},
)

@router.get("/all", response_model=List[company_pydantic])
async def get_companies():
    # sample filtering
    # companies = await Company.filter(date__gte=datetime.now() - timedelta(days=7)).all().values()

    # make sure order by recent creation with created_at
    return await company_pydantic.from_queryset(Company.all().order_by('-created_at'))

# temporarily, lets add a agency list here for now
@router.get("/agencies")
async def get_agencies():
    agencies = await agency_pydantic.from_queryset(Agency.all().order_by('-created_at'))

    return agencies


@router.post("/add")
async def add_company(company_json: str = Form(...)):
    data = json.loads(company_json)

    company = await Company.create(**data)

    # throw exception if company is not created
    # if not company:
    #     raise HTTPException(status_code=500, detail="Company not created")

    return await company_pydantic.from_tortoise_orm(company)

@router.put("/edit")
async def edit_company(company_json: str = Form(...)):
    data = json.loads(company_json)

    data_copy = data.copy()

    data_copy.pop('id')

    company = await Company.filter(id=data['id']).update(**data_copy)

    # throw exception if company is not updated
    if not company:
        raise HTTPException(status_code=500, detail="Company not updated")

    return await Company.get(id=data['id']).values()

@router.delete("/delete")
async def delete_company(company_ids : List[str] = Form(...)):
    deleted_companies = await Company.filter(id__in=company_ids).delete()

    # throw exception if company is not deleted
    if deleted_companies == 0:
        raise HTTPException(status_code=500, detail="Company not deleted")

    return {"deleted_companies": company_ids}

@router.get("/company_select")
async def get_company_selection():
    companies = await Company.all()

    companies_list = [await company_selection_pydantic.from_tortoise_orm(company) for company in companies]

    sorted_companies = sorted(companies_list, key=lambda x: x.name_en)

    return sorted_companies