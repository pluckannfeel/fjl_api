from datetime import datetime, timedelta
import json
import os
import pandas as pd

from typing import List, Type
from app.helpers.s3_file_upload import generate_s3_url, upload_file_to_s3
from app.helpers.generate_docs import fill_application_form, fill_manpower_request_form, fill_employment_contract, fill_recruitment_agreement

# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

from app.models.company import Company, company_pydantic, company_pydantic_in, company_selection_pydantic
from app.models.agency import Agency, agency_pydantic, agency_selection_pydantic
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
async def delete_company(company_ids: List[str] = Form(...)):
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


@router.get("/agency_select")
async def get_agency_selection():
    agencies = await Agency.all()

    agencies_list = [await agency_selection_pydantic.from_tortoise_orm(agency) for agency in agencies]

    sorted_agencies = sorted(agencies_list, key=lambda x: x.name)

    return sorted_agencies


@router.post("/generate_document")
async def generate_document(details: str = Form(...)):
    # async def generate_document(d):
    data = json.loads(details)

    # # check if details has None values, if there is raise an error
    if any(value is None for value in data.values()):
        raise HTTPException(status_code=400, detail="Invalid details")

    company_id = data['selected_company']
    agency_id = data['selected_agency']

    company = await Company.get(id=company_id)
    agency = await Agency.get(id=agency_id)

    # check if company and agency is not found
    if not company or not agency:
        raise HTTPException(
            status_code=404, detail="Company or Agency not found")

    if (data['document_type'] == 'application_form'):
        generated_document = fill_application_form(company, agency, data)

        return generated_document
    elif (data['document_type'] == 'manpower_request'):
        match data['visa_type']:
            case 'psw':
                data['visa_type'] = 'Engineer / Specialist in Humanities / International Services'
            case 'titp':
                data['visa_type'] = 'Technical Intern Training Program'
            case 'ssw':
                data['visa_type'] = 'Specified Skilled Worker'
            case 'student':
                data['visa_type'] = 'Student'
            # case default:
            #     return ''

        generated_document = fill_manpower_request_form(company, agency, data)

        return generated_document
    elif (data['document_type'] == 'employment_contract'):
        generated_document = fill_employment_contract(company, agency, data)

        return generated_document
    elif (data['document_type'] == 'recruitment_agreement'):
        generated_document = fill_recruitment_agreement(company, agency, data)

        return generated_document
    else:
        # throw exception if document type is not found
        raise HTTPException(status_code=404, detail="Document type not found")

    # generated_application_form = fill_application_form([], [], {})
    # generated_manpower_request_form = fill_manpower_request_form([], [], {
    #     'jobDetails': [
    #         {'id': 0, 'title': "Software Engineer",
    #          'no_of_workers': 2, 'basic_salary': "JPY 250000"},
    #         {'id': 1, 'title': "Project Manager",
    #          'no_of_workers': 1, 'basic_salary': "JPY 350000"}
    #     ],
    #     # add total workers dynamically
    #     'totalWorkers': 3
    # })
    # generated_employment_contract = fill_employment_contract([], [], {})

    # array of generated documents
    # documents = [generated_application_form, generated_manpower_request_form, generated_employment_contract]

    # return documents

    # generate document
