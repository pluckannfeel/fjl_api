import json
import os
import io
import re
import chardet
import calendar
import pandas as pd
import requests
import pytz


from typing import List, Type, Optional, Union
from datetime import datetime, timedelta, timezone, time
from io import BytesIO

# env
from dotenv import load_dotenv


# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse

from tortoise.expressions import Q
from tortoise.exceptions import DoesNotExist

# models
from app.models.applicant import Applicant, applicant_pydantic
from app.models.organization import Organization

# schema
from app.models.applicant_schema import ApplicantSchema, UpdateApplicantSchema, CreateApplicantToken

# mailing

# helpers
from app.helpers.s3_file_upload import upload_file_to_s3, generate_s3_url, is_file_exists, upload_image_to_s3
from app.auth.authentication import hash_password, applicant_token_generator, verify_token_applicant_email

# mail
from app.helpers.mailer import Mailer, EmailSchema

from fastapi import FastAPI, Form
# from fastapi.responses import StreamingResponse
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
# from reportlab.lib.units import inch, mm
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Frame, KeepInFrame


s3_applicant_image_upload_folder = 'uploads/applicant/img/'
s3_applicant_photos_upload_folder = 'uploads/applicant/photos/'
s3_applicant_videos_upload_folder = 'uploads/applicant/videos/'
s3_applicant_licenses_upload_folder = 'uploads/applicant/licenses/'

fjl_cdn = 'https://d1l1wfoqw8757j.cloudfront.net/'

router = APIRouter(
    prefix="/applicant",
    tags=["Applicant"],
    responses={404: {"some_description": "Not found"}}
)


@router.get("/all")
async def get_applicants():
    # applicants = await Applicant.all()
    applicants_list = await applicant_pydantic.from_queryset(Applicant.all())

    # Define json fields only once outside the loop
    json_fields = ['family', 'education', 'qualifications_licenses',
                   'unique_questions', 'photos', 'links', 'work_experience', 'required_questions']

    # Use list comprehension to process each applicant
    modified_applicants = [await process_applicant(
        applicant, json_fields) for applicant in applicants_list]

    return modified_applicants


async def process_applicant(applicant, json_fields):
    applicant_dict = applicant.dict()  # Convert Pydantic model to dict

    # Efficiently handle JSON parsing
    for field in json_fields:
        field_value = applicant_dict.get(field)
        if field_value is not None:
            applicant_dict[field] = json.loads(field_value)

    # Modify 'required_questions' if applicable
    if applicant_dict.get('required_questions') is not None:
        modify_required_questions(applicant_dict)

    # Replace the S3 bucket URL with the CDN URL for 'img_url'
    img_url = applicant_dict.get('img_url')
    if img_url:
        applicant_dict['img_url'] = img_url.replace(
            'https://fjl-bucket.s3.amazonaws.com/', fjl_cdn)

    return applicant_dict


# async def get_image_as_base64(url):
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#         return base64.b64encode(response.content).decode('utf-8')


def modify_required_questions(applicant_dict):
    has_family = bool(applicant_dict.get('family'))

    # Prepare the new question
    new_question = {
        "id": "4",
        "question": "日本に友人、知人、親戚がいますか？ (Do you have friends, family/relatives living in Japan?)",
        "answer": "yes" if has_family else "no"
    }

    required_questions = applicant_dict['required_questions']
    if len(required_questions) >= 3:
        required_questions.insert(3, new_question)

        # Update the IDs of the subsequent questions efficiently
        for i in range(4, len(required_questions)):
            required_questions[i]['id'] = str(
                int(required_questions[i]['id']) + 1)


# def customize_styles():
#     styles = getSampleStyleSheet()

#     # styles.add(ParagraphStyle(name='Title', fontSize=24, leading=28, alignment=1, textColor=colors.navy, spaceAfter=6))
#     styles.add(ParagraphStyle(name='Heading', fontSize=14,
#                leading=18, spaceAfter=12, textColor=colors.darkblue))
#     # styles.add(ParagraphStyle(name='BodyText', fontSize=12, leading=14, spaceBefore=6, spaceAfter=6))
#     styles.add(ParagraphStyle(name='BodyTextIndented', leftIndent=10,
#                fontSize=12, leading=14, spaceBefore=6, spaceAfter=6))
#     styles.add(ParagraphStyle(name='TableHeader', fontSize=12, leading=14,
#                textColor=colors.darkblue, bold=True, spaceBefore=12, spaceAfter=6))

#     return styles


# @router.post("/generate_applicant_pdf")
# async def generate_applicant_pdf(data: str = Form(...)):
#     applicant_data = json.loads(data)
#     buffer = BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm,
#                             leftMargin=18*mm, topMargin=12*mm, bottomMargin=12*mm)
#     styles = customize_styles()

#     elements = []

#     # Image and Name
#     if applicant_data['img_url']:
#         try:
#             response = requests.get(applicant_data['img_url'])
#             img_io = BytesIO(response.content)
#             img = Image(img_io)
#             img.drawHeight = 50*mm
#             img.drawWidth = 50*mm
#             img.hAlign = 'CENTER'
#             elements.append(img)
#             elements.append(Spacer(1, 12))
#         except Exception as e:
#             print(f"Failed to load image: {e}")

#     elements.append(Paragraph(
#         f"{applicant_data['first_name']} {applicant_data['last_name']}", styles['Title']))
#     contact_info = f"Email: {applicant_data['email']} | Phone: {applicant_data['phone_number']}"
#     elements.append(Paragraph(contact_info, styles['BodyText']))

#     # Education
#     # elements.append(Paragraph("Education", styles['Heading']))
#     # if 'education' in applicant_data:
#     #     for edu in applicant_data['education']:
#     #         elements.append(Paragraph(
#     #             f"{edu['school_name']} ({edu['from']} - {edu['to']})", styles['BodyTextIndented']))

#     # Education
#     elements.append(Paragraph("Education", styles['Heading']))
#     if 'education' in applicant_data:
#         education_data = [['Date', 'School Name']]
#         for edu in applicant_data['education']:
#             # Formatting dates
#             start_date = edu.get('from', '')
#             end_date = edu.get('to', '')

#             # Formatting school name
#             school_name = edu.get('school_name', '')

#             # Formatting major
#             major = edu.get('major', '')

#             # Constructing the education line
#             education_line = [
#                 f"{start_date[:7]} - {end_date[:7]}", school_name]

#             # Add major if available
#             if major:
#                 education_line.append(f"Major: {major}")

#             education_data.append(education_line)

#         # Define table style
#         table_style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#                                   ('ALIGN', (1, 0), (1, -1), 'LEFT'),
#                                   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#                                   ('SIZE', (0, 0), (-1, -1), 10),
#                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 6)])

#         # Create the table
#         table = Table(education_data)
#         table.setStyle(table_style)

#         elements.append(table)

    # # # Work Experience
    # # elements.append(Paragraph("Work Experience", styles['Heading']))
    # # if 'work_experience' in applicant_data:
    # #     for exp in applicant_data['work_experience']:
    # #         elements.append(Paragraph(
    # #             f"{exp['employer_name']} - {exp['position']} ({exp['from']} - {exp['to']})", styles['BodyTextIndented']))

    # # Define fixed column widths
    # # Divide page width into 8 equal parts for 4 columns
    # col_widths = [doc.width / 8] * 4

    # # Work Experience
    # elements.append(Paragraph("Work Experience", styles['Heading']))
    # if 'work_experience' in applicant_data:
    #     work_exp_data = [['Date', 'Employer', 'Position', 'Responsibilities']]
    #     for exp in applicant_data['work_experience']:
    #         # Formatting dates
    #         start_date = exp.get('from', '')[:7]
    #         end_date = exp.get('to', '')[:7]

    #         # Formatting employer name and position
    #         employer_name = exp.get('employer_name', '')
    #         position = exp.get('position', '')

    #         # Formatting responsibilities
    #         responsibilities = exp.get('responsibilities', '')

    #         # Constructing the work experience line
    #         work_exp_line = [f"{start_date} - {end_date}",
    #                          employer_name, position, responsibilities]

    #         work_exp_data.append(work_exp_line)

    #     # Define table style
    #     table_style = TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    #                               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #                               ('SIZE', (0, 0), (-1, -1), 10),
    #                               ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    #                               # Color header text
    #                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
    #                               # Header background color
    #                               ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
    #                               # Row background color
    #                               ('BACKGROUND', (0, 1),
    #                                (-1, -1), colors.lightgrey),
    #                               ('BOX', (0, 0), (-1, -1), 1, colors.black)])  # Add border around the table

    #     # Create the table
    #     table = Table(work_exp_data, colWidths=col_widths)
    #     table.setStyle(table_style)

    #     elements.append(table)

    # # Qualifications and Licenses
    # elements.append(
    #     Paragraph("Qualifications and Licenses", styles['Heading']))
    # if 'qualifications_licenses' in applicant_data:
    #     for qual in applicant_data['qualifications_licenses']:
    #         elements.append(
    #             Paragraph(f"{qual}", styles['BodyTextIndented']))

    # # Unique Questions
    # elements.append(Paragraph("Unique Questions", styles['Heading']))
    # question_table = []
    # for question in applicant_data.get('unique_questions', []):
    #     question_table.append([question['question'], question['answer']])
    # if question_table:
    #     t = Table(question_table)
    #     t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25,
    #                colors.black), ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))
    #     elements.append(t)

    # # Required Questions
    # if applicant_data['required_questions'] is not None:
    #     elements.append(Paragraph("Required Questions", styles['Heading']))
    #     required_table = []
    #     for question in applicant_data.get('required_questions', []):
    #         required_table.append([question['question'], question['answer']])
    #     if required_table:
    #         t = Table(required_table)
    #         t.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25,
    #                                 colors.black), ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))
    #         elements.append(t)

    # # Additional Personal Statements
    # elements.append(Paragraph("Self Introduction", styles['Heading']))
    # elements.append(
    #     Paragraph(applicant_data['self_introduction'], styles['BodyText']))

    # elements.append(Paragraph("Reason for Application", styles['Heading']))
    # elements.append(
    #     Paragraph(applicant_data['reason_for_application'], styles['BodyText']))

    # elements.append(Paragraph("Past Experience", styles['Heading']))
    # elements.append(
    #     Paragraph(applicant_data['past_experience'], styles['BodyText']))

    # # Build PDF
    # doc.build(elements)
    # buffer.seek(0)
    # return StreamingResponse(buffer, media_type="application/pdf")


# Add Image
    # if applicant_data['img_url']:
    #     try:
    #         response = requests.get(applicant_data['img_url'])
    #         response.raise_for_status()
    #         img_io = BytesIO(response.content)
    #         img = Image(img_io, 2*inch, 2*inch)
    #         img.hAlign = 'CENTER'
    #         elements.append(img)
    #     except requests.RequestException as e:
    #         print(f"Failed to load image: {e}")


# @router.get("/{applicant_id}")
# async def get_applicant(applicant_id: str):
#     # try:

#     # except Exception as e:
#     #     return {"error": str(e)}

#     if not applicant_id:
#         return {}

#     # Fetch the applicant from the database
#     try:
#         applicant = await Applicant.get(id=applicant_id)
#     except DoesNotExist:
#         return HTTPException(status_code=404, detail="Applicant not found")

#     # Convert the ORM model instance to a Pydantic model instance
#     pydantic_applicant = await applicant_pydantic.from_tortoise_orm(applicant)

#     # Convert to dict to manipulate
#     applicant_dict = pydantic_applicant.dict()

#     # Now you can manipulate your data
#     applicant_dict['qualifications_licenses'] = json.loads(
#         applicant_dict['qualifications_licenses'])
#     applicant_dict['photos'] = json.loads(applicant_dict['photos'])
#     applicant_dict['work_experience'] = json.loads(
#         applicant_dict['work_experience'])
#     applicant_dict['education'] = json.loads(applicant_dict['education'])
#     applicant_dict['family'] = json.loads(applicant_dict['family'])
#     # applicant_dict['links'] = json.loads(applicant_dict['links'])
#     applicant_dict['unique_questions'] = json.loads(
#         applicant_dict['unique_questions'])

#     return applicant_dict


@router.get("/get_applicant_info", name="Get applicant by authkey")
async def get_applicant_by_authkey(token: str):

    applicant = await verify_token_applicant_email(token)

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or Expired token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Convert the ORM model instance to a Pydantic model instance
    pydantic_applicant = await applicant_pydantic.from_tortoise_orm(applicant)

    # Convert to dict to manipulate
    applicant_dict = pydantic_applicant.dict()

    # Now you can manipulate your data
    applicant_dict['qualifications_licenses'] = json.loads(
        applicant_dict['qualifications_licenses'])
    # applicant_dict['photos'] = json.loads(applicant_dict['photos'])
    applicant_dict['work_experience'] = json.loads(
        applicant_dict['work_experience'])
    applicant_dict['education'] = json.loads(applicant_dict['education'])
    applicant_dict['family'] = json.loads(applicant_dict['family'])
    # applicant_dict['links'] = json.loads(applicant_dict['links'])
    applicant_dict['unique_questions'] = json.loads(
        applicant_dict['unique_questions'])

    applicant_dict['required_questions'] = json.loads(
        applicant_dict['required_questions'])

    has_family = applicant_dict['family'] is not None and len(
        applicant_dict['family']) > 0

    if ('required_questions' in applicant_dict):
        # on applicant_dict['unique_questions'] add has_family
        # New question to be inserted
        new_question = {
            "id": "4",
            "question": "日本に友人、知人、親戚がいますか？ (Do you have friends, family/relatives living in Japan?)",
            "answer": "yes" if has_family else "no"
        }

        # Insert the new question at the fourth position
        # Insert at index 3, which is the fourth position
        applicant_dict['required_questions'].insert(3, new_question)

        # Update the IDs of the subsequent questions
        # Start from index 4 since we inserted at index 3
        for i in range(4, len(applicant_dict['required_questions'])):
            applicant_dict['required_questions'][i]['id'] = str(
                int(applicant_dict['required_questions'][i]['id']) + 1)  # Increment IDs by 1

    if applicant_dict['photos']:
        applicant_dict['photos'] = json.loads(applicant_dict['photos'])

    return applicant_dict


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_applicant(login_info: CreateApplicantToken) -> dict:
    token = await applicant_token_generator(login_info.email, login_info.password)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
            headers={'WWW-Authenticate": "Bearer'}
        )

    return {'token': token, 'email': login_info.email, 'msg': "user logged in."}


@router.post("/create_applicant")
async def create_applicant(
        applicant_json: str = Form(...),
        display_photo: UploadFile = File(...),
        licenses: List[UploadFile] = File([]),
        # licenses: Optional[List[UploadFile]] = None,
        photos: List[UploadFile] = File([])):

    try:
        # Parse the JSON string back into a dictionary
        applicant_data = json.loads(applicant_json)
        print("Loaded JSON data (applicant_data)", )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail="Incorrect JSON format in applicant data.")

    # Construct the Applicant instance manually
    applicant = ApplicantSchema(
        applicant_json=applicant_data,
        display_photo=display_photo,
        licenses=licenses,
        photos=photos
    )

    details = applicant.applicant_json

    print("Instanced ApplicantSchema (applicant) called details")

    # extract the password from the details details["password"]
    # then hash the password as password_hash
    details["password_hash"] = hash_password(details["password"])
    # pop the password from the details
    details.pop("password")

    # we will add the image url, files to the details after we upload the files to s3
    now = datetime.now()

    # Upload the display photo to S3
    if applicant.display_photo is not None:
        # image_name = details['first_name'] + \
        #     details['last_name'] + '_dp_' + now.strftime("_%Y%m%d_%H%M%S") + \
        #     '.' + applicant.display_photo.filename.split('.')[-1]
        image_name = f"{details['last_name']}_{details['first_name']}_dp_{now.strftime('%Y%m%d_%H%M%S')}.jpg"

        # upload
        upload_file_to_s3(applicant.display_photo, image_name,
                          s3_applicant_image_upload_folder)

        s3_img_path = s3_applicant_image_upload_folder + image_name

        s3_read_url = generate_s3_url(s3_img_path, 'read')

        # append to details
        details['img_url'] = s3_read_url
        print("Successfully uploaded display photo to s3")

    if details['work_experience'] is not None:
        details['work_experience'] = json.dumps(
            details['work_experience'])

        print("Successfully stringified work experience to json")

    if details['education'] is not None:
        details['education'] = json.dumps(details['education'])

        print("Successfully stringified education to json")

    if details['family'] is not None:
        details['family'] = json.dumps(details['family'])

        print("Successfully stringified family to json")

    if details['unique_questions'] is not None:
        details['unique_questions'] = json.dumps(
            details['unique_questions'])

        print("Successfully stringified unique questions to json")

    if details['required_questions'] is not None:
        details['required_questions'] = json.dumps(
            details['required_questions'])

        print("Successfully stringified required questions to json")

    # if details['links'] is not None:
    #     details['links'] = json.dumps(details['links'])

    # licenses
    if applicant.licenses is not None:
        if 'qualifications_licenses' not in details:
            details['qualifications_licenses'] = []

        for file in applicant.licenses:

            new_file_name = file.filename.split(
                '.')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]

            upload_file_to_s3(file, new_file_name,
                              s3_applicant_licenses_upload_folder)

            s3_file_path = s3_applicant_licenses_upload_folder + new_file_name

            s3_read_url = generate_s3_url(s3_file_path, 'read')

            details['qualifications_licenses'][applicant.licenses.index(
                file)]['file'] = s3_read_url

        # dump the details to json
        details['qualifications_licenses'] = json.dumps(
            details['qualifications_licenses'])

        print("Successfully uploaded licenses to s3")

    # photos
    # if applicant.photos is not None:
    #     if 'photos' not in details:
    #         details['photos'] = []

    #     for file in applicant.photos:

    #         new_file_name = file.filename.split(
    #             '.')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]

    #         upload_file_to_s3(file, new_file_name,
    #                           s3_applicant_photos_upload_folder)

    #         s3_file_path = s3_applicant_photos_upload_folder + new_file_name

    #         s3_read_url = generate_s3_url(s3_file_path, 'read')

    #         details['photos'].append(s3_read_url)

    #     # dump the details to json
    #     details['photos'] = json.dumps(details['photos'])

    # modified apr 10
    # Handling photos that could be images or videos
    if applicant.photos:
        if 'photos' not in details:
            details['photos'] = []

        for file in applicant.photos:
            # Determine the appropriate folder based on the file type
            is_video = file.content_type.startswith('video/')

            folder_path = s3_applicant_videos_upload_folder if is_video else s3_applicant_photos_upload_folder

            file_type_label = 'video' if is_video else 'pic'
            # Retrieve first_name and last_name from the details
            first_name = details.get('first_name', 'unknown')
            last_name = details.get('last_name', 'unknown')

            # new_file_name = f"{file.filename.split('.')[0]}{now.strftime('_%Y%m%d_%H%M%S')}.{file.filename.split('.')[-1]}"
            new_file_name = f"{first_name}_{last_name}_{file_type_label}_{now.strftime('%Y%m%d_%H%M%S')}.{file.filename.split('.')[-1]}"
            upload_file_to_s3(file, new_file_name, folder_path)
            s3_file_path = folder_path + new_file_name
            s3_read_url = generate_s3_url(s3_file_path, 'read')

            details['photos'].append(s3_read_url)

        # Dump the photo URLs to JSON
        details['photos'] = json.dumps(details['photos'])

        print("Successfully uploaded photos to s3")

    # Create the applicant instance
    applicant = await Applicant.create(**details)

    new_applicant = await applicant_pydantic.from_tortoise_orm(applicant)

    return new_applicant

    # Here, you would typically save the applicant data to your database
    # For now, let's just return a simple confirmation
    # return {"msg": "Applicant created successfully", "applicant": applicant}


@router.put("/admin_edit_applicant")
async def admin_edit_applicant(data: str = Form(...)):
    applicant_info = json.loads(data)

    # print(applicant_info)

    # Fetch the applicant from the database using the ID

    try:
        applicant = await Applicant.get(id=applicant_info['id'])
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Applicant not found.")

    # Make a copy of applicant_info, remove the id and Update the applicant
    data_copy = applicant_info.copy()

    # pop id
    data_copy.pop('id')

    # Update the applicant
    updated = await Applicant.filter(id=applicant_info['id']).update(**data_copy)

    if not updated:
        raise HTTPException(
            status_code=500, detail="There was an error updating the applicant.")

    return {"msg": "Applicant updated successfully."}


@router.put("/update_applicant")
async def update_applicant(applicant_json: str = Form(...), display_photo: UploadFile = File(None), licenses: List[Union[UploadFile, str]] = []):
    print("dp: ", display_photo)
    try:
        # Parse the JSON string back into a dictionary
        applicant_data = json.loads(applicant_json)
        # print("Loaded JSON data (applicant_data)", applicant_data)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail="Incorrect JSON format in applicant data.")

    applicant = UpdateApplicantSchema(
        applicant_json=applicant_data,
        display_photo=display_photo,
        licenses=licenses,
    )

    details = applicant.applicant_json

    now = datetime.now()
    if display_photo is not None:
        # image_name = applicant_data['first_name'] + \
        #     applicant_data['last_name'] + '_dp_' + \
        #     datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
        image_name = f"{details['last_name']}_{details['first_name']}_dp_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        # image_name = f"{details['id']}_"

        # upload_file_to_s3(display_photo, image_name,
        #                   s3_applicant_image_upload_folder)

        # s3_img_path = s3_applicant_image_upload_folder + image_name

        upload_file_to_s3(display_photo, image_name,
                          s3_applicant_image_upload_folder)

        s3_img_path = s3_applicant_image_upload_folder + image_name

        s3_read_url = generate_s3_url(s3_img_path, 'read')

        details['img_url'] = s3_read_url
        print("Successfully uploaded display photo to s3")

    if details['work_experience'] is not None:
        details['work_experience'] = json.dumps(
            details['work_experience'])

        print("Successfully stringified work experience to json")

    if details['education'] is not None:
        details['education'] = json.dumps(details['education'])

        print("Successfully stringified education to json")

    if details['family'] is not None:
        details['family'] = json.dumps(details['family'])

        print("Successfully stringified family to json")

    if details['unique_questions'] is not None:
        details['unique_questions'] = json.dumps(
            details['unique_questions'])

        print("Successfully stringified unique questions to json")

    if details['required_questions'] is not None:
        details['required_questions'] = json.dumps(
            details['required_questions'])

        print("Successfully stringified required questions to json")

    if applicant.licenses is not None:
        if 'qualifications_licenses' not in details:
            details['qualifications_licenses'] = []

        for file in applicant.licenses:
            print(file)
            # check first if the file is a string, if it is, it means there is already a file uploaded, so do nothing
            if isinstance(file, str):
                pass
            else:
                new_file_name = file.filename.split(
                    '.')[0] + now.strftime("_%Y%m%d_%H%M%S") + '.' + file.filename.split('.')[-1]

                upload_file_to_s3(file, new_file_name,
                                  s3_applicant_licenses_upload_folder)

                s3_file_path = s3_applicant_licenses_upload_folder + new_file_name

                s3_read_url = generate_s3_url(s3_file_path, 'read')

                details['qualifications_licenses'][applicant.licenses.index(
                    file)]['file'] = s3_read_url

        # dump the details to json
        details['qualifications_licenses'] = json.dumps(
            details['qualifications_licenses'])

        print("Successfully uploaded licenses to s3")

    data_copy = details.copy()

    # print("Data copy: ", data_copy)

    # pop id
    data_copy.pop('id')
    # pop password
    data_copy.pop('password')
    data_copy.pop('has_family')

    # Update the applicant
    updated = await Applicant.filter(id=details['id']).update(**data_copy)

    if not updated:
        raise HTTPException(
            status_code=500, detail="There was an error updating the applicant.")

    return {"msg": "Applicant updated successfully."}


def create_forgot_password_email_body(token):
    return f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1, h2 {{ color: #333366; }}
                p {{ margin: 10px 0; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ margin: 5px 0; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h2>サイトアクセスについてのご案内</h2>
            <p>以下のトークンを使用してサイトにアクセスしてください：</p>
            <p><strong>{token}</strong></p>
            <p>ミライロをご利用いただき、ありがとうございます。</p>
            <br>
            <h2>Instructions for Site Access</h2>
            <p>Please access the site using the following token:</p>
            <p><strong>{token}</strong></p>
            <p>Thank you for using Mirairo.</p>
            <br>
            <p>Thank you very much,<br>Mirairo</p>
        </body>
    </html>
    """


@router.post("/forgot_password")
async def applicant_forgot_password(email: str = Form(...)):
    # check if email exists
    try:
        applicant = await Applicant.get(email=email)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Applicant not found.")

    # generate token
    # token = await applicant_token_generator(email, applicant.password_hash)
    token = applicant.password_hash

    # send email
    mailer = Mailer()
    # mailer.send_email(email, token)

    msg_body = create_forgot_password_email_body(token)

    mail_details = EmailSchema(
        email=[email,],
        body=msg_body,
        subject="Mirairo Password Reset | ミライロ パスワードリセット"
    )

    try:
        await mailer.send_email(mail_details)
        print("Email sent successfully.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="There was an error sending the email.", error=str(e))

    return {"msg": "Email sent successfully."}


@router.post("/forgot_password_submit")
async def applicant_forgot_password(submit_json: str = Form(...)):
    # loads the json string to a dictionary
    data = json.loads(submit_json)

    # check if credentials exist
    try:
        applicant = await Applicant.get(password_hash=data["code"])

        # hash the new password
        new_password_hash = hash_password(data["new_password"])

        # update the password of the applicant
        updated = await Applicant.filter(id=applicant.id
                                         ).update(password_hash=new_password_hash)

        if not updated:
            raise HTTPException(
                status_code=500, detail="There was an error updating the password.")

        return {"code": "password_updated", "msg": "Password updated successfully."}

    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Applicant not found.")
