from datetime import datetime, timedelta
import json
import os
import pandas as pd

from typing import List, Type
from app.helpers.s3_file_upload import generate_s3_url, upload_file_to_s3
from app.helpers.generate_docs import fill_application_form, fill_manpower_request_form, fill_employment_contract, fill_recruitment_agreement,generate_default_documents, fill_ssw_company_profile, fill_ssw_list_task_duties, generate_letter_pack

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
    data = json.loads(details)

    # Replace None values with empty strings
    for key, value in data.items():
        if value is None:
            data[key] = ""

    # Generate default documents for specific document types
    if data['document_type'] in ['aqium_license_copy', 'aqium_representative_passport_copy', 'psw_initial_checklist', 'ssw_initial_checklist']:
        return generate_default_documents(data['document_type'], data['application_type'])

    
    # Fetch company and agency for other document types
    # check if selected_agency is present in the data
    if data.get('selected_agency') is not None:
        agency_id = data.get('selected_agency')
        agency = await Agency.get(id=agency_id)
    else:
        # set default agency
        agency = await Agency.get(id='550e8400-e29b-41d4-a716-446655440000')

    company_id = data.get('selected_company')
    company = await Company.get(id=company_id)
        
    if not company or not agency:
        raise HTTPException(status_code=404, detail="Company or Agency not found")

    # Handle different document types
    if data['document_type'] == 'application_form':
        return fill_application_form(company, agency, data)
    elif data['document_type'] == 'manpower_request':
        visa_mapping = {
            'psw': 'Engineer / Specialist in Humanities / International Services',
            'titp': 'Technical Intern Training Program',
            'ssw': 'Specified Skilled Worker',
            'student': 'Student'
        }
        data['visa_type'] = visa_mapping.get(data['visa_type'], data['visa_type'])
        return fill_manpower_request_form(company, agency, data)
    elif data['document_type'] == 'employment_contract':
        return fill_employment_contract(company, agency, data)
    elif data['document_type'] == 'recruitment_agreement':
        return fill_recruitment_agreement(company, agency, data)
    elif data['document_type'] == 'company_profile':
        # ssw company profile
        return fill_ssw_company_profile(company, agency, data)
    elif data['document_type'] == 'task_qualification_list':
        # ssw list of tasks and qualifications
        return fill_ssw_list_task_duties(company, agency, data)
    elif data['document_type'] == 'letter_pack':
        # Configuration for each sheet with the corresponding keys
        sheet_configs = {
            'MYS 日本語': {
                'sender_name_key': company.name_ja,
                'sender_rep_name_key': f"{company.rep_position_ja} {company.rep_name_ja}",
                'sender_address_key': f"{company.prefecture_ja} {company.municipality_town_ja} {company.street_address_ja} {company.building_ja}",
                'sender_address_key2': "",
                'sender_tel_key': company.phone,
            },
            'MYS 英語': {
                'sender_name_key': company.name_en,
                'sender_rep_name_key': f"{company.rep_position_en} {company.rep_name_en}",
                'sender_address_key': f"{company.building_en} {company.street_address_ja} {company.municipality_town_en} ",
                'sender_address_key2': f"{company.prefecture_en} JAPAN",
                'sender_tel_key': company.phone,
            }
        }

        return generate_letter_pack(data, sheet_configs)
    else:
        raise HTTPException(status_code=404, detail="Document type not found")

