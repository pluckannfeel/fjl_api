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

# env
from dotenv import load_dotenv


# fast api
from fastapi import APIRouter, status, HTTPException, File, Form, UploadFile, Response
from fastapi.responses import JSONResponse, FileResponse

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

s3_applicant_image_upload_folder = 'uploads/applicant/img/'
s3_applicant_photos_upload_folder = 'uploads/applicant/photos/'
s3_applicant_videos_upload_folder = 'uploads/applicant/videos/'
s3_applicant_licenses_upload_folder = 'uploads/applicant/licenses/'

router = APIRouter(
    prefix="/applicant",
    tags=["Applicant"],
    responses={404: {"some_description": "Not found"}}
)


@router.get("")
async def get_applicants():
    applicants = await Applicant.all()
    return applicants


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